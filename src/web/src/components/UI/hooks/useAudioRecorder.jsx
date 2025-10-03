import axios from 'axios';
import { useCallback, useEffect, useRef, useState } from 'react';
import { AUDIO_SETTINGS, SERVER_URL } from '../../../config';
import { useWebSocketContext } from '../../../contexts/WebSocketContext';

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

    const lastAverageRef = useRef(0);
    const consecutiveSilenceFramesRef = useRef(0);
    const consecutiveAudioFramesRef = useRef(0);

    const { socket, emit } = useWebSocketContext();

    const initializeAudioContext = useCallback(() => {
        if (!audioContextRef.current) {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                audioContextRef.current = new AudioContext();

                if (audioContextRef.current.state === 'suspended') {
                    audioContextRef.current.resume();
                }

                analyserRef.current = audioContextRef.current.createAnalyser();
                analyserRef.current.fftSize = 256;
                console.log('AudioContext initialized successfully');
                return true;
            } catch (error) {
                console.error('Error initializing audio context:', error);
                return false;
            }
        }
        return true;
    }, []);

    useEffect(() => {
        isWaitingResponseRef.current = isWaitingResponse;

        if (isWaitingResponseRef.current && isRecordingRef.current) {
            console.log('Waiting for response, stopping recording...');
            stopRecording();
        }
    }, [isWaitingResponse])

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecordingRef.current) {
            console.log('🛑 Stopping recording...');
            isRecordingRef.current = false;
            mediaRecorderRef.current.stop()
            setIsRecording(false);

            if (silenceTimerRef.current) {
                cancelAnimationFrame(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }

            silenceStartTimeRef.current = null;
            consecutiveSilenceFramesRef.current = 0;
            consecutiveAudioFramesRef.current = 0;
        }
    }, []);

    const detectSilence = useCallback((stream) => {

        if (!initializeAudioContext()) {
            console.error('Failed to initialize audio context');
            return;
        }

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

                consecutiveSilenceFramesRef.current++;
                consecutiveAudioFramesRef.current = 0;

                if (!silenceStartTimeRef.current) {
                    silenceStartTimeRef.current = Date.now();
                    console.log(`🔇 SILENCE DETECTED - Timer init (avg: ${average.toFixed(2)}, threshold: ${silenceThreshold.current})`);
                } else {
                    const silenceDuration = Date.now() - silenceStartTimeRef.current;
                    const remainingTime = silenceDurationRef.current - silenceDuration;

                    if (consecutiveSilenceFramesRef.current % 60 === 0) {
                        console.log(`⏱️  Silence: ${(silenceDuration / 1000).toFixed(1)}s / ${(silenceDurationRef.current / 1000).toFixed(1)}s ( ${(remainingTime / 1000).toFixed(1)}s remaining)`);
                    }

                    if (silenceDuration >= silenceDurationRef.current) {
                        console.log(`✅ SILENCE THRESHOLD REACHED - Stopping recording (${(silenceDuration / 1000).toFixed(1)}s of silence)`);
                        stopRecording();
                        return;
                    }
                }
            } else {
                consecutiveAudioFramesRef.current++;

                if (silenceStartTimeRef.current !== null) {
                    const interruptedAfter = Date.now() - silenceStartTimeRef.current;
                    console.log(`🔊 AUDIO DETECTED - Silence timer RESET after ${(interruptedAfter / 1000).toFixed(1)}s (avg: ${average.toFixed(2)})`);
                    silenceStartTimeRef.current = null;
                    consecutiveSilenceFramesRef.current = 0;
                }

                if (consecutiveAudioFramesRef.current % 180 === 0) {
                    console.log(`🎤 Audio detected, continuing recording... (avg: ${average.toFixed(2)})`)
                }
            }
            silenceTimerRef.current = requestAnimationFrame(checkSilence);
        };

        console.log('🎧 Starting silence detection...');
        silenceTimerRef.current = requestAnimationFrame(checkSilence);
    }, [stopRecording, initializeAudioContext]);

    const startRecording = useCallback(async () => {
        if (isWaitingResponseRef.current || isRecordingRef.current || isSpeaking) {
            console.log('❌ Recording unable to start:', {
                isWaiting: isWaitingResponseRef.current,
                isRecording: isRecordingRef.current,
                isSpeaking
            });
            return;
        }

        try {
            console.log('🎤 Starting recording...');
            audioChunksRef.current = [];
            silenceStartTimeRef.current = null;
            consecutiveSilenceFramesRef.current = 0;
            consecutiveAudioFramesRef.current = 0;

            if (!navigator.mediaDevices || !window.MediaRecorder) {
                console.error('❌ MediaDevices or MediaRecorder not supported');
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
                    console.log(`⏰ Max recording time reached`);
                    stopRecording();
                }
            }, AUDIO_SETTINGS.maxRecordingTime);

            mediaRecorderRef.current.onstop = async () => {
                clearTimeout(maxRecordingTime);
                const audioBlob = new Blob(audioChunksRef.current, { type: AUDIO_SETTINGS.mimeType });

                console.log(`📦 Failed recording - Size: ${(audioBlob.size / 1024).toFixed(2)} KB, Chunks: ${audioChunksRef.current.length}`);

                if (audioChunksRef.current.length > 0) {
                    await handleTranscribe(audioBlob);
                }
                stream.getTracks().forEach(track => track.stop());
            };
            isRecordingRef.current = true;
            mediaRecorderRef.current.start(100);
            setIsRecording(true);

            console.log('✅ Successfully started recording');

            detectSilence(stream);
        } catch (error) {
            console.error('❌ Error starting recording:', error);
            return;
        }
    }, [detectSilence, stopRecording, isSpeaking]);

    useEffect(() => {
        return () => {
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                audioContextRef.current.close();
            }
        };
    }, []);

    const handleTranscribe = async (audioBlob) => {
        try {

            if (isWaitingResponseRef.current) {
                console.log('⏸️  Waiting for response, canceling transcription');
                return;
            }

            if (!audioBlob || audioBlob.size === 0) {
                console.log('⚠️ No audio blob to transcribe');
                return;
            }

            isWaitingResponseRef.current = true;

            const actualBlob = audioBlob.blob || audioBlob;
            console.log(`🔄 Transcribing audio blob of size: ${(actualBlob.size / 1024).toFixed(2)} KB`);

            const reader = new FileReader();
            reader.readAsDataURL(actualBlob);

            reader.onloadend = async () => {
                const base64Audio = reader.result.split(',')[1];

                if (socket && socket.connected) {
                    const messageObject = {
                        type: 'audio',
                        data: base64Audio,
                        socketId: socket.id
                    };
                    emit('client_message', messageObject);

                    console.log('📤 Audio sent via socket for transcription and processing');
                } else {
                    console.error('❌ Socket not connected, cannot send audio');
                }

            };
        } catch (error) {
            console.error('Error transcribing audio:', error);
        } finally {
            isWaitingResponseRef.current = false;
        }
    };

    const handleSynthesize = async (text) => {
        if (!text) return;

        try {
            setIsSpeaking(true);
            console.log('🔊 Synthesizing speech...');

            const response = await axios.post(`${SERVER_URL}/api/synthesize`, { text: text });

            if (response.data && response.data.audioContent) {
                const audioContent = response.data.audioContent;
                const audioSrc = `data:audio/wav;base64,${audioContent}`;
                setAudioSrc(audioSrc);

                const audio = new Audio(audioSrc);
                audio.onerror = (e) => {
                    console.error('Error playing audio:', e);
                    setIsSpeaking(false);
                    setAudioSrc(null);
                }

                audio.onended = () => {
                    console.log('✅ Audio playback finished');
                    setIsSpeaking(false);
                    setAudioSrc(null);
                }

                await audio.play();
            }
        } catch (error) {
            console.error('❌ Error synthesizing speech:', error);
            setIsSpeaking(false);
            setAudioSrc(null);
        } finally {
            setIsSpeaking(false);
        }

    };

    handleSynthesize.cancel = () => {
        setIsSpeaking(false);
        setAudioSrc(null);
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
        handleTranscribe,
        handleSynthesize,
        onStop
    };
};

export default useAudioRecorder;