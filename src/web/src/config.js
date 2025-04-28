export const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8081';
export const AUDIO_SETTINGS = {
    mimeType: 'audio/webm',
    bufferSize: 2048,
    sampleRate: 44100,
    silenceThreshold: 20,
    silenceDuration: 2000,
    maxTimeRecording: 90000,
    audioBitsPerSecond: 16000
};
export const ANIMATION_MAPPINGS = {
    joy: 'Joy',
    joy_blush: 'Blush',
    neutrañ: 'Hello',
    sad: 'Sad',
    silly: 'Yes',
    surprise: 'Attention',
    angry: 'Angry'
};