import axios from 'axios';
import { useCallback, useEffect, useRef, useState } from 'react';
import { AUDIO_SETTINGS, SERVER_URL } from '../../../config';

const useAudioRecorder = (onTranscriptionComplete, isWaitingResponse) => {
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
    const silenceDurationRef = useRef(AUDIO_SETTINGS.silenceDuration);
    const isRecordingRef = useRef(false);
    const isWaitingResponseRef = useRef(isWaitingResponse);
    const isTranscribingRef = useRef(false);

    useEffect(() => {
        isWaitingResponseRef.current = isWaitingResponse;

        if (isWaitingResponseRef.current && isRecordingRef.current) {
            console.log('Waiting for response, stopping recording...');
            stopRecording();
        }
    }, [isWaitingResponse])

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecordingRef.current) {
            isRecordingRef.current = false;
            mediaRecorderRef.current.stop()
            setIsRecording(false);

            if (silenceTimerRef.current) {
                cancelAnimationFrame(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }
        }
    }, []);

    const detectSilence = useCallback((stream) => {
        if (!audioContextRef.current || !analyserRef.current || isWaitingResponseRef.current) return;

        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const checkSilence = () => {
            if (!isRecordingRef.current || isWaitingResponseRef.current) {
                console.log('Recording stopped, stopping silence detection...');
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
                if (!silenceStartTimeRef.current) {
                    silenceStartTimeRef.current = Date.now();
                    console.log('Silence detected, starting timer at:', silenceStartTimeRef.current);
                } else {
                    const silenceDuration = Date.now() - silenceStartTimeRef.current;
                    if (silenceDuration >= silenceDurationRef.current) {
                        console.log('Silence duration exceeded, stopping recording...');
                        stopRecording();
                        return;
                    }
                }
            } else {
                silenceStartTimeRef.current = null;
            }
            silenceTimerRef.current = requestAnimationFrame(checkSilence);
        };
        silenceTimerRef.current = requestAnimationFrame(checkSilence);
    }, [stopRecording]);

    const startRecording = useCallback(async () => {
        if (isWaitingResponse.current || isRecordingRef.current || isSpeaking) return;
        try {
            audioChunksRef.current = [];
            silenceStartTimeRef.current = null;

            if (!navigator.mediaDevices || !window.MediaRecorder) {
                console.error('MediaDevices or MediaRecorder API not supported');
                return;
            }

            const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 48000 } });
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
                if (isRecordingRef.current) {
                    stopRecording();
                    console.log('Max recording time exceeded, stopping recording...');
                }
            }, AUDIO_SETTINGS.maxRecordingTime);
            mediaRecorderRef.current.onstop = async () => {
                clearTimeout(maxRecordingTime);
                const audioBlob = new Blob(audioChunksRef.current, { type: AUDIO_SETTINGS.mimeType });

                if (audioChunksRef.current.length > 0) {
                    await handleTranscribe(audioBlob);
                }
                stream.getTracks().forEach(track => track.stop());
            };
            isRecordingRef.current = true;
            mediaRecorderRef.current.start(100);
            setIsRecording(true);
            detectSilence(stream);
        } catch (error) {
            console.error('Error starting recording:', error);
        }
    }, [detectSilence, stopRecording]);

    const handleTranscribe = async (audioBlob) => {
        try {

            if (isTranscribingRef.current) return;

            if (!audioBlob || audioBlob.size === 0) {
                console.warn('Received invalid or empty audio blob:', audioBlob);
                return;
            }

            isTranscribingRef.current = true;

            const actualBlob = audioBlob.blob || audioBlob;
            console.log('Transcribing audio blob of size:', actualBlob.size, 'bytes');

            const reader = new FileReader();
            reader.readAsDataURL(actualBlob);

            reader.onloadend = async () => {
                const base64Audio = reader.result.split(',')[1];
                const response = await axios.post(`${SERVER_URL}/api/transcribe`, { audio: base64Audio });
                console.log('Audio sended to server for transcription');
                if (response.data) {
                    setTranscribedText(response.data);
                    if (onTranscriptionComplete) {
                        onTranscriptionComplete(transcribedText);
                        console.log('Transcription completed:', transcribedText);
                    }
                }
            };
        } catch (error) {
            console.error('Error transcribing audio:', error);
        } finally {
            isTranscribingRef.current = false;
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

                const audio = new Audio(audioSrc);
                audio.onerror = (e) => {
                    console.error('Error playing audio:', e);
                    setIsSpeaking(false);
                }
                await audio.play();
            }
        } catch (error) {
            console.error('Error synthesizing speech:', error);
            setIsSpeaking(false);
        }

    };

    handleSynthesize.cancel = () => {
        setIsSpeaking(false);
        setAudioSrc('');
    };

    const onStop = () => {
        setIsSpeaking(false);
    };

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

    return {
        isRecording,
        transcribedText,
        audioSrc,
        isSpeaking,
        startRecording,
        stopRecording,
        handleTranscribe,
        handleSynthesize,
        onStop
    };
};

export default useAudioRecorder;