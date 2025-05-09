import PropTypes from 'prop-types';
import React, { useEffect, useRef, useState } from 'react';
import { ANIMATION_MAPPINGS } from "../../config";
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import '../../styles/InterfaceStyle.css';
import FaceDetection from '../FaceDetection';
import useAudioRecorder from './hooks/useAudioRecorder';
import AudioControls from './subcomponents/AudioControls';
import ChatWindow from './subcomponents/ChatWindow';
import StatusBar from './utils/StatusBar';

const Interface = ({ sharedStream, animationIndex, setAnimationIndex, animations }) => {
    // Main states
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [isChatVisible, setIsChatVisible] = useState(true);
    const [connectionError, setConnectionError] = useState(false);
    const [isWaitingResponse, setIsWaitingResponse] = useState(false);
    const [faceDetected, setFaceDetected] = useState(false);

    // Context and references
    const { isConnected, isRegistered, emit, socket } = useWebSocketContext();
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
        handleSynthesize
    } = useAudioRecorder(() => {
        setIsWaitingResponse(false);
    }, isWaitingResponse);

    useEffect(() => {
        setConnectionError(!isConnected);
    }, [isConnected]);

    const handleRobotMessage = async (message) => {
        if (message.state) {
            console.log("Received robot state:", message.state);
            const animationName = ANIMATION_MAPPINGS[message.state] || "Attention";
            const index = animations.findIndex((animation) => animation === animationName);
            if (index !== -1) {
                setAnimationIndex(index);
            }
        }

        if (message.text?.trim()) {
            console.log("Received robot message:", message.text);
            setMessages((messages) => [...messages, { text: message.text, sender: 'robot' }]);
            await handleSynthesize(message.text);
        }
        setIsWaitingResponse(false);
    };

    const handleWizardMessage = async (message) => {
        if (message.state) {
            const animationName = ANIMATION_MAPPINGS[message.state] || "Attention";
            const index = animations.findIndex((animation) => animation === animationName);
            if (index !== -1) {
                setAnimationIndex(index);
            }
        }
        setMessages(prev => [...prev, { text: message.text, sender: 'wizard' }]);
        await handleSynthesize(message.text);
        setIsWaitingResponse(false);
    };

    const handleClientMessage = (message) => {
        if (message.text?.trim()) {
            setMessages((messages) => [...messages, { text: message.text, sender: 'client' }]);
        }
    };

    useEffect(() => {
        if (socket) {
            socket.on('robot_message', handleRobotMessage);
            socket.on('wizard_message', handleWizardMessage);
            socket.on('client_message', handleClientMessage);

            return () => {
                socket.off('robot_message', handleRobotMessage);
                socket.off('wizard_message', handleWizardMessage);
                socket.off('client_message', handleClientMessage);
            };
        }
    }, [socket])

    const handleFaceDetected = () => {
        setFaceDetected(true);
        if (!isRecording && !isWaitingResponse && !isSpeaking) {
            startRecording();
        }
    };

    const handleFaceLost = () => {
        setFaceDetected(false);
        if (isRecording) {
            stopRecording();
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
        if (transcribedText && isConnected) {
            setMessages(prev => [...prev, { text: transcribedText, sender: 'client' }]);

            const messageObject = {
                type: "client_message",
                text: transcribedText,
                proactive_question: "Ninguna",
                username: "Desconocido"
            };
            const success = emit('client_message', messageObject);
            setIsWaitingResponse(success);
        }
    }, [transcribedText, isConnected, emit]);

    useEffect(() => {
        if (!isWaitingResponse && !isRecording && !isSpeaking && faceDetected) {
            const timer = setTimeout(() => {
                startRecording();
            }, 1000);

            return () => clearTimeout(timer);
        }

    }, [isWaitingResponse, isRecording, isSpeaking, faceDetected, startRecording]);

    const handleSendMessage = () => {
        if (newMessage.trim() && isConnected) {
            const messageObject = {
                type: "client_message",
                text: newMessage,
                proactive_question: "Ninguna",
                username: "Desconocido"
            };

            const success = emit('client_message', messageObject);

            if (success) {
                setIsWaitingResponse(success);
                setMessages((messages) => [...messages, { text: newMessage, sender: 'client' }]);
                setNewMessage('');
                setTimeout(scrollToBottom, 100);
            } else {
                setMessages((messages) => [...messages, {
                    text: "No se pudo enviar el mensaje. Comprueba tu conexión.",
                    sender: 'robot'
                }]);
            }
        }
    };

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
                onMessageSend={handleSendMessage}
                onInputChange={(e) => setNewMessage(e.target.value)}
            >
                <div className="chat-controls">
                    <AudioControls
                        isRecording={isRecording}
                        isSpeaking={isSpeaking}
                        isWaitingResponse={isWaitingResponse}
                        onStartRecording={startRecording}
                        onStopRecording={stopRecording}
                    />
                    <StatusBar
                        isRegistered={isRegistered}
                        connectionError={connectionError}
                        isSpeaking={isSpeaking}
                        isWaitingResponse={isWaitingResponse}
                        audioSrc={audioSrc}
                        faceDetected={faceDetected}
                    />
                    <FaceDetection
                        onFaceDetected={handleFaceDetected}
                        onFaceLost={handleFaceLost}
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