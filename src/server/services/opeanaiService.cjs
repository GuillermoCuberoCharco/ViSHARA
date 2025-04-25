const OpenAI = require('openai');
const { loadPrompt } = require('../utils/promptLoader.cjs');
const config = require('../config/environment.cjs');

const openai = new OpenAI({
    apiKey: config.openai.apiKey
});

const SYSTEM_PROMPT = loadPrompt();

async function getOpenAIResponse(input, context = {}) {
    const now = new Date();
    const formattedDate = `${now.getDate().toString.padStart(2, '0')}-
    ${(now.getMonth() + 1).toString().padStart(2, '0')}-
    ${now.getFullYear()} ${now.getHours().toString().padStart(2, '0')}:
    ${now.getMinutes().toString().padStart(2, '0')}`;
    const message = [
        { role: "system", content: SYSTEM_PROMPT },
        //...get_full_conversation_history(), // For historical context, future feature
        {
            role: "user", content: JSON.stringify({
                user_input: input,
                timestamp: formattedDate,
                username: context.username || "Desconocido",
                proactive_question: context.proactive_question || "Ninguna"
            })
        }
    ];

    try {
        console.log("Sending message to OpenAI:", JSON.stringify(message[1].content));
        const completion = await openai.chat.completions.create({
            model: "gpt-4o",
            messages: message,
            response_format: { type: "json_object" },
            temperature: 1,
            top_p: 1
        });

        const responseContent = completion.choices[0].message.content;
        console.log("Received response from OpenAI:", responseContent);

        const parsedResponse = JSON.parse(responseContent);

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