
const fs = require('fs');
const path = require('path');
const { Translate } = require('@google-cloud/translate').v2;
const AssistantV2 = require('ibm-watson/assistant/v2');
const NaturalLanguageUnderstandingV1 = require('ibm-watson/natural-language-understanding/v1');
const { IamAuthenticator } = require('ibm-watson/auth');
require('dotenv').config();

process.env.GOOGLE_APPLICATION_CREDENTIALS = 'vishara-415010-002552ca9ca0.json';

const apiKey = process.env.ASSISTANT_APIKEY;
const assistantId = process.env.ASSISTANT_LIVE_ENV_ID;
const serviceUrl = process.env.ASSISTANT_URL;
const nluApiKey = process.env.NLU_APIKEY;
const nluUrl = process.env.NLU_URL;

const translateClient = new Translate();

const assistantAuthenticator = new IamAuthenticator({ apikey: apiKey });
const assistant = new AssistantV2({
    version: '2020-04-01',
    authenticator: assistantAuthenticator,
    serviceUrl: serviceUrl,
});

let sessionId;

assistant.createSession({ assistantId })
    .then(res => {
        console.log("Session created successfully", res.result);
        sessionId = res.result.session_id;
    })
    .catch(err => {
        console.log("Failed to create session", err);
    });

const nluAuthenticator = new IamAuthenticator({ apikey: nluApiKey });
const nlu = new NaturalLanguageUnderstandingV1({
    version: '2020-08-01',
    authenticator: nluAuthenticator,
    serviceUrl: nluUrl,
});

const SESSION_TIME = 20;
let lastQueryTime = null;

async function translateText(text, target) {
    const [translation] = await translateClient.translate(text, target);
    return translation;
}

function createSession() {
    return assistant.createSession({ assistantId })
        .then(res => {
            sessionId = res.result.session_id;
        });
}

function isSessionActive() {
    return lastQueryTime !== null && (Date.now() - lastQueryTime) / 1000 < SESSION_TIME;
}

async function analyzedMood(text) {
    try {
        const trasnlatedText = await translateText(text, 'en');
        console.log('Text translated:', trasnlatedText);

        const nluOptions = {
            text: trasnlatedText,
            features: {
                emotion: {},
            },
            language: 'en'
        };


        const response = await nlu.analyze(nluOptions);
        const emotions = response.result.emotion.document.emotion;
        const strongestEmotion = getStrongestEmotion(emotions);
        console.log('Emotions: ', emotions);
        console.log('Strongest emotion:', strongestEmotion);
        return { emotions, strongestEmotion };
    } catch (error) {
        console.error('Error analyzing mood:', error);
        return { emotions: null, strongestEmotion: null };
    }
}

function getStrongestEmotion(emotions) {
    if (!emotions || Object.keys(emotions).length === 0) {
        return null;
    }

    const threshold = {
        low: 0.1,
        medium: 0.3,
        high: 0.6,
    };

    const emotionToStateMap = {
        sadness: 'Sad',
        joy: 'Joy',
        fear: 'Attention',
        disgust: 'No',
        anger: 'Angry'
    };

    let strongestEmotion = '';
    let maxScore = -Infinity;

    for (const [emotion, score] of Object.entries(emotions)) {
        if (score > maxScore) {
            maxScore = score;
            strongestEmotion = emotion;
        }
    }

    if (maxScore < threshold.low) {
        return 'Attention';
    } else if (maxScore < threshold.medium) {
        if (strongestEmotion === 'joy') {
            return 'Joy';
        } else {
            return emotionToStateMap[strongestEmotion] || 'Attention';
        }
    } else if (maxScore < threshold.high) {
        return emotionToStateMap[strongestEmotion] || 'Attention';
    } else {
        if (strongestEmotion === 'joy') {
            return 'Blush';
        } else if (strongestEmotion === 'sadness' || strongestEmotion === 'fear') {
            return 'Sad';
        } else {
            return emotionToStateMap[strongestEmotion] || 'Attention';
        }
    }
}

async function getWatsonResponse(inputText) {
    try {
        if (!sessionId || isSessionActive()) {
            console.log('Creating new session');
            await createSession();
        }

        const response = await assistant.message({
            assistantId: assistantId,
            sessionId: sessionId,
            input: {
                message_type: 'text',
                text: inputText,
            }
        });

        console.log('Watson response:', response.result);
        const context = response.result.context || {};
        const skill = context.skills || {};
        const mainSkill = skill['main skill'] || {};
        const userDefined = mainSkill.user_defined || {};
        const { emotions, strongestEmotion } = await analyzedMood(inputText);

        lastQueryTime = Date.now();

        return { response: response.result, userDefined, emotions, strongestEmotion };
    } catch (error) {
        console.error('Error getting Watson response:', error);
        if (error.code === 404 && error.message.includes('session')) {
            console.log('Session expired, creating new session');
            await createSession();
            return getWatsonResponse(inputText);
        }
        throw error;
    }
}



module.exports = {
    createSession,
    isSessionActive,
    getWatsonResponse,
    getStrongestEmotion
};