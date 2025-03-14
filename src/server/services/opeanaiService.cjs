const OpenAI = require('openai');
const { loadPrompt } = require('../utils/promptLoader.cjs');
const config = require('../config/environment.cjs');

const openai = new OpenAI({
    apiKey: config.openai.apiKey
});

const SYSTEM_PROMPT = loadPrompt();

async function getOpenAIResponse(input, context = {}) {
    const message = [
        { role: "system", content: SYSTEM_PROMPT },
        //...get_full_conversation_history(), // For historical context, future feature
        {
            role: "user", content: JSON.stringify({
                ...context,
                user_input: input,
                timestamp: new Date().toISOString("es-ES")
            })
        }
    ];

    try {
        const response = await openai.chat.completions.create({
            model: "gpt-4o",
            messages: message,
            response_format: { type: "json_object" },
            temperature: 1,
            top_p: 1
        });

        const parsedResponse = JSON.parse(response.data.choices[0].message.content);

        return {
            continue: parsedResponse.continue,
            robot_mood: parsedResponse.robot_mood,
            text: parsedResponse.response || ""
        };

    } catch (error) {
        console.error('Error getting OpenAI response:', error);
        return {
            continue: false,
            robot_mood: "Sad",
            text: ""
        };
    }
}

module.exports = { getOpenAIResponse };