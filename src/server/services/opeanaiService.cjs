const OpenAI = require('openai');
const { loadPrompt } = require('../utils/promptLoader.cjs');
const config = require('../config/environment.cjs');

const openai = new OpenAI({
    apiKey: config.openai.apiKey
});

const SYSTEM_PROMPT = loadPrompt();

async function getOpenAIResponse(input, context = {}, conversationHistory = []) {
    const now = new Date();
    const formattedDate = `${now.getDate().toString().padStart(2, '0')}-${(now.getMonth() + 1).toString().padStart(2, '0')}-${now.getFullYear()} ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

    try {
        let conversationContext = "";
        if (conversationHistory && conversationHistory.length > 0) {
            conversationContext = "\n\nHISTORIAL DE CONVERSACIONES ANTERIORES:\n";
            conversationContext += "=== CONVERSACIONES PREVIAS ===\n";

            conversationHistory.forEach((msg, index) => {
                const role = msg.role === 'user' ? 'USUARIO' : 'SHARA';
                const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleString('es-ES') : '';
                conversationContext += `[${timestamp}] ${role}: ${msg.content}\n`;
            });

            conversationContext += "=== FIN DEL HISTORIAL ===\n";
            conversationContext += "INTRUCCIONES: Usa este historial para recordar conversaciones anteriores y hacer la conversación más personal y coherente. Puedes referenciar temas, experiencias o información que el usuario haya compartido contigo anteriormente. Hazlo de manera natural, no como si estuvieras leyendo una lista.\n\n";
        }

        const enhancedSystemPrompt = SYSTEM_PROMPT + conversationContext;

        const message = [
            { role: "system", content: enhancedSystemPrompt },
            {
                role: "user", content: JSON.stringify({
                    user_input: input,
                    timestamp: formattedDate,
                    username: context.username || "Desconocido",
                    proactive_question: context.proactive_question || "Ninguna"
                })
            }
        ];

        console.log("Sending message to OpenAI with conversation history:", {
            inputLength: input.length,
            historyMessages: conversationHistory.length,
            username: context.username,
            proactiveQuestion: context.proactive_question
        });

        const completion = await openai.chat.completions.create({
            model: "gpt-4.1 nano",
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
            text: "Lo siento, he tenido un pequeño problema técnico. ¿Podrías repetir lo que me dijiste?"
        };
    }
}

module.exports = { getOpenAIResponse };