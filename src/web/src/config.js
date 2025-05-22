export const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8081';
export const AUDIO_SETTINGS = {
    mimeType: 'audio/webm;codecs=opus',
    bufferSize: 2048,
    sampleRate: 44100,
    silenceThreshold: 40,
    silenceDuration: 2000,
    maxRecordingTime: 40000,
    audioBitsPerSecond: 16000
};
export const ANIMATION_MAPPINGS = {
    joy: 'Joy',
    joy_blush: 'Blush',
    neutral: 'Hello',
    sad: 'Sad',
    silly: 'Yes',
    surprise: 'Attention',
    angry: 'Angry'
};