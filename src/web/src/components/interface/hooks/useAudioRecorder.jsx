import axios from 'axios';
import { useCallback, useEffect, useRef, useState } from 'react';
import { AUDIO_SETTINGS, SERVER_URL } from '../../../config';

const useAudioRecorder = (onTranscriptionComplete) => {
    const [isRecording, setIsRecording] = useState(false);
    const [audioSrc, setAudioSrc] = useState(null);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [transcribedText, setTranscribedText] = useState(null);

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const silenceTimerRef = useRef(null);
    const silenceStartTimeRef = useRef(null);
    const silenceThreshold = useRef(AUDIO_SETTINGS.silenceThreshold);
    const silenceDuration = useRef(AUDIO_SETTINGS.silenceDuration);

    useEffect(() => {
        if (!audioContextRef.current) {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                audioContextRef.current = new AudioContext();
                analyserRef.current = audioContextRef.current.createAnalyser();
                analyserRef.current.fftSize = 256;
            } catch (error) {
                console.error('Error initializing audio context:', error);
            }
        }

        return () => {
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                audioContextRef.current.close();
            }
        };
    }, []);

    const detectSilence = useCallback((stream) => {
        if (!audioContextRef.current || !analyserRef.current) return;

        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const checkSilence = () => {
            if (!isRecording) {
                cancelAnimationFrame(silenceTimerRef.current);
                silenceTimerRef.current = null;
                return;
            }

            analyserRef.current.getByteFrequencyData(dataArray);

            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const average = sum / bufferLength;

            if (average < silenceThreshold.current) {
                if (!silenceTimerRef.current) {
                    silenceStartTimeRef.current = Date.now();
                    console.log('Silence detected, starting timer...');
                } else if (Date.now() - silenceStartTimeRef.current > silenceDuration.current) {
                    console.log('Silence duration exceeded, stopping recording...');
                    stopRecording();
                    return;
                }
            } else {
                silenceStartTimeRef.current = null;
            }
            silenceTimerRef.current = requestAnimationFrame(checkSilence);
        };
        silenceTimerRef.current = requestAnimationFrame(checkSilence);
    }, [isRecording, stopRecording]);

    const startRecording = useCallback(async () => {
        try {
            audioChunksRef.current = [];
            silenceStartTimeRef.current = null;
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream, {
                mimeType: AUDIO_SETTINGS.mimeType,
                audioBitsPerSecond: AUDIO_SETTINGS.audioBitsPerSecond
            });
            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };
            const maxRecordingTime = setTimeout(() => {
                if (isRecording) {
                    stopRecording();
                }
            }, AUDIO_SETTINGS.maxRecordingTime);
            mediaRecorderRef.current.onstop = async () => {
                clearTimeout(maxRecordingTime);
                const audioBlob = new Blob(audioChunksRef.current, { type: AUDIO_SETTINGS.mimeType });

                if (audioChunksRef.current.length > 0) {
                    const audioUrl = URL.createObjectURL(audioBlob);
                    setAudioSrc(audioUrl);

                    await handleTranscribe(audioBlob);
                }
                stream.getTracks().forEach(track => track.stop());
            };
            mediaRecorderRef.current.start();
            setIsRecording(true);
            detectSilence(stream);
        } catch (error) {
            console.error('Error starting recording:', error);
        }
    }, [detectSilence, isRecording, stopRecording]);

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop()
            setIsRecording(false);

            if (silenceTimerRef.current) {
                cancelAnimationFrame(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }
        }
    }, [isRecording]);

    const handleTranscribe = async (audioBlob) => {
        try {
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);

            reader.onloadend = async () => {
                const base64Audio = reader.result.split(',')[1];
                const response = await axios.post(`${SERVER_URL}/api/transcribe`, { audio: base64Audio });
                if (response.data) {
                    setTranscribedText(response.data);
                    if (onTranscriptionComplete) {
                        onTranscriptionComplete(response.data);
                    }
                }
            };
        } catch (error) {
            console.error('Error transcribing audio:', error);
        }
    };

    const handleSynthesize = async (text) => {
        if (!text) return;

        try {
            setIsSpeaking(true);

            const response = await axios.post(`${SERVER_URL}/api/synthesize`, { text: text });

            if (response.data && response.data.audioContent) {
                const audioContent = response.data.audioContent;
                const audioSrc = `data:audio/wav;base64,${audioContent}`;
                setAudioSrc(audioSrc);
            }
        } catch (error) {
            console.error('Error synthesizing speech:', error);
        } finally {
            setIsSpeaking(false);
        }
    };

    handleSynthesize.cancel = () => {
        setIsSpeaking(false);
        setAudioSrc('');
    };

    const handleAudioStop = (blob) => {
        if (blob) {
            setAudioSrc(URL.createObjectURL(blob));
        }
    };

    const onStop = () => {
        setIsSpeaking(false);
    };

    return {
        isRecording,
        transcribedText,
        audioSrc,
        isSpeaking,
        startRecording,
        stopRecording,
        handleAudioStop,
        handleTranscribe,
        handleSynthesize,
        onStop
    };
};

export default useAudioRecorder;