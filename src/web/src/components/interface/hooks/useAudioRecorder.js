import axios from 'axios';
import { useCallback, useRef, useState } from 'react';
import { AUDIO_SETTINGS, SERVER_URL } from '../../../config';

const useAudioRecorder = (onTranscriptioComplete) => {
    const [isRecording, setIsRecording] = useState(false);
    const [audioSrc, setAudioSrc] = useState(null);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [transcribedText, setTranscribedText] = useState(null);
    const audioContext = useRef(null);
    const analyser = useRef(null);
    const dataArray = useRef(null);
    const silenceCounter = useRef(0);
    const recordedBlob = useRef(null);

    const initializedAudioContext = useCallback(() => {
        if (!audioContext.current) {
            audioContext.current = new (window.AudioContext || window.webkitAudioContext)();
            analyser.current = audioContext.current.createAnalyser();
            analyser.current.fftSize = 256;
            dataArray.current = new Uint8Array(analyser.current.frequencyBinCount);
        }
    }, []);

    const analyzeAudio = useCallback((recordedBlob) => {
        if (!analyser.current || !dataArray.current) return;

        analyser.current.getByteFrequencyData(dataArray.current);
        const volume = dataArray.current.reduce((sum, value) => sum + value, 0) / dataArray.current.length;

        if (volume < AUDIO_SETTINGS.silenceThreshold) {
            silenceCounter.current += 1;
            if (silenceCounter.current > AUDIO_SETTINGS.silenceDuration / 50) {
                stopRecording();
                silenceCounter.current = 0;
            }
        } else {
            silenceCounter.current = 0;
        }

        if (isRecording) {
            requestAnimationFrame(() => analyzeAudio(recordedBlob));
        }
    }, [isRecording]);

    const startRecording = useCallback(() => {
        initializedAudioContext();
        setIsRecording(true);
        silenceCounter.current = 0;
    }, [initializedAudioContext]);

    const stopRecording = useCallback(() => {
        setIsRecording(false);
    }, []);

    const blobToBase64 = useCallback(async (blob) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onerror = reject;
            reader.onload = () => {
                resolve(reader.result.split(",")[1]);
            };
            reader.readAsDataURL(blob);
        });
    }, []);

    const handleTranscribe = useCallback(async (blob) => {
        try {
            const audio = await blobToBase64(blob);
            const response = await axios.post(`${SERVER_URL}/api/transcribe`, { audio });
            setTranscribedText(response.data.text);
            return response.data.text;
        } catch (error) {
            console.error('Error transcribing audio:', error);
            setTranscribedText(null);
            return null;
        }
    }, []);

    const handleSynthesize = useCallback(async (message) => {
        if (!message?.trim()) return;

        try {
            setIsSpeaking(true);
            const response = await axios.post(`${SERVER_URL}/api/synthesize`, { text: message });
            setAudioSrc(`data:audio/mp3;base64,${response.data.audioContent}`);
        } catch (error) {
            console.error('Error synthesizing audio:', error);
        } finally {
            setIsSpeaking(false);
        }
    }, []);

    const handleAudioStop = useCallback(async (blob) => {
        await handleTranscribe(blob);
        onTranscriptioComplete?.();
    }, [handleTranscribe, onTranscriptioComplete]);

    const onStop = useCallback(async (recordedBlob) => {
        if (recordedBlob?.blob) {
            await handleTranscribe(recordedBlob.blob);
        }
    }, [handleTranscribe])

    return {
        isRecording,
        audioSrc,
        isSpeaking,
        transcribedText,
        startRecording: useCallback(() => setIsRecording(true), []),
        stopRecording: useCallback(() => setIsRecording(false), []),
        onStop,
        handleAudioStop,
        handleTranscribe,
        handleSynthesize
    };
};

export default useAudioRecorder;