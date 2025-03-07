import React from 'react';
import { ReactMic } from 'react-mic';
import { AUDIO_SETTINGS } from '../../../config';

const AudioControls = ({
    isRecording,
    isSpeaking,
    isWaitingResponse,
    onStartRecording,
    onStopRecording,
    onAudioStop
}) => (
    <div className="audio-controls">
        <ReactMic
            record={isRecording}
            className="sound-wave"
            onStop={onAudioStop}
            onData={() => { }}
            strokeColor="#000000"
            backgroundColor="#FF4081"
            mimeType={AUDIO_SETTINGS.mimeType}
            bufferSize={AUDIO_SETTINGS.bufferSize}
            sampleRate={AUDIO_SETTINGS.sampleRate}
        />

        <button
            onClick={isRecording ? onStopRecording : onStartRecording}
            disable={isSpeaking || isWaitingResponse}
            className={`record-button ${isRecording ? 'recording' : ''}`}
        >
            {isRecording ? "⏹ Detener grabación" : "⏺ Iniciar grabación"}
        </button>
    </div>
);

AudioControls.propTypes = {
    isRecording: PropTypes.bool.isRequired,
    isSpeaking: PropTypes.bool.isRequired,
    isWaitingResponse: PropTypes.bool.isRequired,
    onStartRecording: PropTypes.func.isRequired,
    onStopRecording: PropTypes.func.isRequired,
    onAudioStop: PropTypes.func.isRequired
};

export default AudioControls;