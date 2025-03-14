const fs = require('fs').promises;
const path = require('path');
const synthesize = require('../src/googleTTS.cjs');

const inputFile = process.argv[2];

if (!inputFile) {
    console.error('Uso: node tts-client.js ruta/al/archivo.txt');
    process.exit(1);
}

const audioDir = path.join(__dirname, 'audios');

async function processFile() {
    try {
        await fs.mkdir(audioDir, { recursive: true });
        const content = await fs.readFile(inputFile, 'utf-8');
        const phrases = content.split('\n').filter(phrase => phrase.trim());

        for (const [index, phrase] of phrases.entries()) {
            if (!phrase.trim()) continue;

            const mockReq = { body: { text: phrase } };
            const mockRes = {
                json: async (data) => {
                    const fileName = `audio_${(index + 1).toString().padStart(3, '0')}.wav`;
                    const filePath = path.join(audioDir, fileName);

                    const audioBuffer = Buffer.from(data.audioContent, 'base64');
                    await fs.writeFile(filePath, audioBuffer);

                    console.log(`✅ Generado: ${fileName} - "${phrase.substring(0, 50)}${phrase.length > 50 ? '...' : ''}"`);
                }
            };

            await synthesize(mockReq, mockRes);
            // Pequeña pausa para no sobrecargar la API
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        console.log(`\n📁 Archivos guardados en: ${audioDir}`);
    } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
    }
}

processFile();