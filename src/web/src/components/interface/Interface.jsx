import PropTypes from 'prop-types';
import React, { useEffect, useRef, useState } from 'react';
import { ANIMATION_MAPPINGS } from '../../config';
import { useCharacterAnimations } from '../../contexts/CharacterAnimations';
import '../../styles/InterfaceStyle.css';
import FaceDetection from '../FaceDetection';
import useAudioRecorder from './hooks/useAudioRecorder';
import useWebSocket from './hooks/useWebSocket';
import AudioControls from './subcomponents/AudioControls';
import ChatWindow from './subcomponents/ChatWindow';
import StatusBar from './utils/StatusBar';

const Interface = ({ sharedStream }) => {
    // Main states
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [isChatVisible, setIsChatVisible] = useState(true);
    const [isRegistered, setIsRegistered] = useState(false);
    const [connectionError, setConnectionError] = useState(false);
    const [isWaitingResponse, setIsWaitingResponse] = useState(false);

    // Context and references
    const { animations, setAnimationIndex } = useCharacterAnimations();
    const messagesContainerRef = useRef(null);
    const waitTimer = useRef(null);

    // Audio hooks and handlers
    const {
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
    } = useAudioRecorder(() => {
        setIsWaitingResponse(false);
    });

    const websocketHandlers = {

        handleRegistrationSuccess: (data) => {
            console.log('Registration successful');
            setIsRegistered(true);
            setConnectionError(false);
        },

        handleRobotMessage: (message) => {
            const animationName = ANIMATION_MAPPINGS[message.state] || 'Attention';
            setAnimationIndex(animations.findIndex((animation) => animation.name === animationName));

            if (message.text?.trim()) {
                setMessages((messages) => [...messages, { text: message.text, sender: 'robot' }]);
            }
            setIsWaitingResponse(false);
        },

        handleWizardMessage: async (message) => {
            setMessages(prev => [...prev, { text: message.text, sender: 'wizard' }]);
            await handleSynthesize(message.text);
            setIsWaitingResponse(false);
        },

        handleClientMessage: (message) => {
            if (message.text?.trim()) {
                setMessages((messages) => [...messages, { text: message.text, sender: 'client' }]);
            }
        },

        handleConnectError: (error) => {
            console.log('Error connecting to server: ', error);
            setConnectionError(error.message || 'Error de conexión');
            setIsRegistered(false);
        },

        handleSocketError: (error) => {
            console.log('Socket error: ', error);
            setConnectionError(true);
            setIsRegistered(false);
        }
    };

    const socket = useWebSocket(websocketHandlers);

    const handleFaceDetected = () => {
        if (!isRecording && !isWaitingResponse && !isSpeaking) {
            startRecording();
        }
    };

    const scrollToBottom = () => {
        if (messagesContainerRef.current) {
            const scrollContainer = messagesContainerRef.current;
            scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        const audioElement = document.querySelector('audio');
        if (audioElement) {
            audioElement.onended = () => handleSynthesize.cancel();
        }
    }, [audioSrc, handleSynthesize]);

    useEffect(() => {
        if (transcribedText && socket) {
            setMessages(prev => [...prev, { text: transcribedText, sender: 'client' }]);

            const messageObject = {
                type: "client_message",
                text: transcribedText,
                proactive_question: "Ninguna",
                username: "Desconocido"
            };
            socket.emit('client_message', messageObject);
        }
    }, [transcribedText, socket]);

    return (
        <div className="chat-wrapper">
            <button
                className="toggle-chat-button"
                onClick={() => setIsChatVisible(!isChatVisible)}
            >
                {isChatVisible ? '🗨️ Ocultar chat' : '🗨️ Mostrar chat'}
            </button>
            <ChatWindow
                messages={messages}
                newMessage={newMessage}
                messagesContainerRef={messagesContainerRef}
                isChatVisible={isChatVisible}
                onMessageSend={() => {
                    if (newMessage.trim()) {
                        const messageObject = {
                            type: "client_message",
                            text: newMessage,
                            proactive_question: "Ninguna",
                            username: "Desconocido"
                        };
                        socket.emit('client_message', messageObject);

                        setMessages((messages) => [...messages, { text: newMessage, sender: 'client' }]);

                        setNewMessage('');

                        setTimeout(scrollToBottom, 100);
                    }
                }}
                onInputChange={(e) => setNewMessage(e.target.value)}
            >
                <div className="chat-controls">
                    <AudioControls
                        isRecording={isRecording}
                        isSpeaking={isSpeaking}
                        isWaitingResponse={isWaitingResponse}
                        onStartRecording={startRecording}
                        onStopRecording={stopRecording}
                        onAudioStop={handleAudioStop}
                    />
                    <StatusBar
                        isRegistered={isRegistered}
                        connectionError={connectionError}
                        isSpeaking={isSpeaking}
                        isWaitingResponse={isWaitingResponse}
                        audioSrc={audioSrc}
                    />
                    <FaceDetection
                        onFaceDetected={handleFaceDetected}
                        stream={sharedStream}
                    />
                </div>
            </ChatWindow>
            <audio src={audioSrc} autoPlay />
        </div>

    );
};

Interface.propTypes = {
    sharedStream: PropTypes.instanceOf(MediaStream)
};

export default Interface;