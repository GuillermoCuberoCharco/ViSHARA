const fs = require('fs');
const path = require('path');

function loadPrompt() {
    try {
        return fs.readFileSync(
            path.resolve('./files/shara_prompt.txt'),
            'utf-8'
        );
    } catch (error) {
        console.error('Error loading prompt:', error);
        return "Eres un asistente amigable. Responde de manera natural y conversacional"
    }
}

module.exports = { loadPrompt };