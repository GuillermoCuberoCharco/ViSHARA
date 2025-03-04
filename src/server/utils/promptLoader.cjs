import fs from 'fs';
import path from 'path';

export function loadPrompt() {
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