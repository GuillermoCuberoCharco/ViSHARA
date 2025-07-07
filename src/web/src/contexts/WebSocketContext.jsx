import { createContext, useContext, useEffect, useRef, useState } from "react";
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

        if (!socketRef.current || !socketRef.current.connected) {

            const newSocket = io(SERVER_URL, {
                path: '/message-socket',
                transports: ['websocket', 'polling'],
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                timeout: 20000,
                autoConnect: true
            });

            socketRef.current = newSocket;
        }

        const socket = socketRef.current;

        socket.removeAllListeners();

        socket.on('connect', () => {
            console.log('WebSocket connected with id:', socket.id);
            setIsConnected(true);
            socket.emit('register_client', { client: 'web', type: 'participant', userAgent: navigator.userAgent, timestamp: Date.now() });
        });

        socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            setIsConnected(false);
            setIsRegistered(false);

            setTimeout(() => {
                if (socket.current && !socket.connected) {
                    socket.connect();
                }
            }, 1000);
        });

        socket.on('registration_success', (data) => {
            console.log('WebSocket registered successfully');
            setIsRegistered(true);
            if (handlers && handlers.handleRegistrationSuccess) {
                handlers.handleRegistrationSuccess();
            }
        });

        if (handlers) {
            if (handlers.handleRobotMessage) {
                socket.on('robot_message', (message) => {
                    console.log('Received robot message:', message);
                    try {
                        handlers.handleRobotMessage(message);
                    } catch (error) {
                        console.error('Error handling robot message:', error);
                    }
                });
            }

            if (handlers.handleWizardMessage) {
                socket.on('wizard_message', (message) => {
                    console.log('Received wizard message:', message);
                    try {
                        handlers.handleWizardMessage(message);
                    } catch (error) {
                        console.error('Error handling wizard message:', error);
                    }
                });
            }

            if (handlers.handleClientMessage) {
                socket.on('client_message', (message) => {
                    console.log('Sended client message:', message);
                    try {
                        handlers.handleClientMessage(message);
                    } catch (error) {
                        console.error('Error handling client message:', error);
                    }
                });
            }

            if (handlers.handleConnectError) {
                socket.on('connect_error', (error) => {
                    console.error('WebSocket connection error:', error);
                    try {
                        handlers.handleConnectError(error);
                    } catch (error) {
                        console.error('Error handling error message:', error);
                    }
                });
            }
        }

        socket.on('ui_state_sync', (data) => {
            console.log('UI state sync received:', data);
            if (handlers?.handleUIStateSync) {
                handlers.handleUIStateSync(data);
            }
        });

        socket.on('robot_animation_sync', (data) => {
            console.log('Robot animation sync received:', data);
            if (handlers?.handleRobotAnimationSync) {
                handlers.handleRobotAnimationSync(data);
            }
        });

        socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Reconnecting... Attempt ${attemptNumber}`);
        });

        socket.on('reconnect', () => {
            console.log('Reconnected to WebSocket');
            socket.emit('register_client', { client: 'web' });
        });

        socket.on('error', (error) => {
            console.error('WebSocket error:', error);
        });

        return () => {
            console.log('Cleaning up WebSocket connection...');
            if (socketRef.current) {
                socketRef.current.removeAllListeners();
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
        id: socketRef.current?.id,

        emitUIStateChange: (stateData) => {
            if (socketRef.current && socketRef.current.connected) {
                socketRef.current.emit('ui_state_change', stateData);
            }
        },
        emitRobotAnimation: (animationData) => {
            if (socketRef.current && socketRef.current.connected) {
                socketRef.current.emit('robot_animation_trigger', animationData);
            }
        }
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
};