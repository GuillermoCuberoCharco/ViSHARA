import axios from 'axios';
import React, { useState } from 'react';

function App(){
    const [text, setText] = useState('');
    const [audioSrc, setAudioSrc] = useState(null);

    const handleSynthesize = async () => {
        const response = await axios.post("http://localhost:3000/synthesize", { text, });
        const audioSrc = `data:audio/mp3;base64,${response.data.audioContent}`;
        setAudioSrc(audioSrc);
      };

    return(
        <div style={{marginLeft:'100px'}}>
            <h1>Prueba de síntesis de voz</h1>
            <textarea value={text} onChange={e => setText(e.target.value)} placeholder="Introduce el texto"></textarea>
            <br />
            <button onClick={handleSynthesize}>Sintetizar</button>
            <br />
            {audioSrc && <audio controls src={audioSrc}/>}
        </div>
    )
}

export default App;