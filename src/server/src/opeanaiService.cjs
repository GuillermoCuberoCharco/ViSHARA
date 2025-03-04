const OpenAI = require('openai');
const { loadPrompt } = require('./utils/promptLoader.cjs');

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

const SYSTEM_PROMPT = loadPrompt();

async function getOpenAIResponse(input, context = {}) {
    const message = [
        { role: "system", content: SYSTEM_PROMPT },
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

        return JSON.parse(response.data.choices[0].message.content);
    } catch (error) {
        console.error('Error getting OpenAI response:', error);
        return {
            continue: false,
            robot_mood: "Sad",
            text: "Vaya, creo que estoy teniendo problemas técnicos. ¿Podríamos intentarlo de nuevo?"
        };
    }
}

module.exports = { getOpenAIResponse };