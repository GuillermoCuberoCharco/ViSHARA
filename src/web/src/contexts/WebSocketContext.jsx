import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../config";

const WebSocketContext = createContext(null);

export const useWebSocketContext = () => {
    const context = useContext(WebSocketContext);
    if (!context) {
        throw new Error("useWebSocketContext must be used within a WebSocketProvider");
    }
    return context;
};

export const WebSocketProvider = ({ children, handlers }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isRegistered, setIsRegistered] = useState(false);
    const socketRef = useRef(null);

    useEffect(() => {
        console.log('Initializing WebSocket connection at:', SERVER_URL);

        const newSocket = io(SERVER_URL, {
            path: '/message-socket',
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 20000,
            forceNew: true,
            autoConnect: true
        });

        socketRef.current = newSocket;

        const setupEventListeners = () => {
            console.log('Setting up event listeners...');

            newSocket.on('connect', () => {
                console.log('WebSocket connected with id:', newSocket.id);
                setIsConnected(true);
                newSocket.emit('register_client', { client: 'web' });
            });

            newSocket.on('disconnect', (reason) => {
                console.log('WebSocket disconnected:', reason);
                setIsConnected(false);
                setIsRegistered(false);

                if (reason === 'io server disconnect') {
                    newSocket.connect();
                }
            });

            newSocket.on('registration_success', () => {
                console.log('WebSocket registered successfully');
                setIsRegistered(true);
                if (handlers && handlers.handleRegistrationSuccess) {
                    handlers.handleRegistrationSuccess();
                }
            });

            if (handlers) {
                if (handlers.handleRobotMessage) {
                    newSocket.on('robot_message', (message) => {
                        console.log('Received robot message:', message);
                        handlers.handleRobotMessage(message);
                    });
                }

                if (handlers.handleWizardMessage) {
                    newSocket.on('wizard_message', (message) => {
                        console.log('Received wizard message:', message);
                        handlers.handleWizardMessage(message);
                    });
                }

                if (handlers.handleClientMessage) {
                    newSocket.on('client_message', (message) => {
                        console.log('Sended client message:', message);
                        handlers.handleClientMessage(message);
                    });
                }

                if (handlers.handleConnectError) {
                    newSocket.on('connect_error', (error) => {
                        console.error('WebSocket connection error:', error);
                        handlers.handleConnectError(error);
                    });
                }
            }

            newSocket.on('reconnect_attempt', (attemptNumber) => {
                console.log(`Reconnecting... Attempt ${attemptNumber}`);
            });
        };

        setupEventListeners();

        return () => {
            console.log('Cleaning up WebSocket connection...');
            if (socketRef.current) {
                socketRef.current.removeAllListeners();
                socketRef.current.disconnect();
                socketRef.current = null;
            }
        };
    }, [handlers]);

    const emit = (event, data) => {
        if (socketRef.current && socketRef.current.connected) {
            socketRef.current.emit(event, data);
            return true;
        } else {
            console.error('WebSocket is not connected');
            return false;
        }
    };

    const value = {
        socket: socketRef.current,
        isConnected,
        isRegistered,
        emit,
        id: socketRef.current?.id
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
};