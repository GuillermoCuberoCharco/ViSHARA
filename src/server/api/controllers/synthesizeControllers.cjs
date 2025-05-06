const { synthesizeText } = require('../../services/googleTTS.cjs');

async function handleSynthesize(req, res) {
    try {
        const text = req.body.text;

        if (!text) {
            return res.status(400).json({ error: 'Text is required' });
        }

        const audioContent = await synthesizeText(text);
        res.json({ audioContent });
    } catch (error) {
        console.error('Error in synthesizeText:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
}

module.exports = { handleSynthesize };
//hola guille tu puedes animoooooooooooooooooo