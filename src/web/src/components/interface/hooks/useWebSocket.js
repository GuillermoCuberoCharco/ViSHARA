import { useEffect, useRef, useState } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../../../config";

const useWebSocket = (handlers) => {
    const [socket, setSocket] = useState(null);
    const socketRef = useRef(null);

    useEffect(() => {
        console.log('Connecting to server at:', SERVER_URL);
        const newSocket = io(SERVER_URL, {
            path: '/message-socket',
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 20000,
            forceNew: true,
            autoConnect: true
        });

        console.log('New socket created:', newSocket.id);

        socketRef.current = newSocket;
        setSocket(newSocket);
        console.log('Socket set:', newSocket.id);

        const setupEventListeners = () => {
            console.log('Setting up event listeners');
            newSocket.on('connect', () => {
                console.log('Connected to server with ID:', newSocket.id);
                newSocket.emit('register_client', 'web');
            });

            newSocket.on('disconnect', (reason) => {
                console.log('Disconnected from server:', reason);
                if (reason === 'io server disconnect') {
                    newSocket.connect();
                }
            })

            newSocket.on('registration_success', (data) => {
                console.log('Registration success:', data);
                handlers.handleRegistrationSuccess(data);
            });
            newSocket.on('robot_message', handlers.handleRobotMessage);
            newSocket.on('wizard_message', handlers.handleWizardMessage);
            newSocket.on('client_message', handlers.handleClientMessage);
            newSocket.on('connect_error', handlers.handleConnectError);
            newSocket.on('error', handlers.handleSocketError);

            newSocket.on('reconnect_attempt', (attemptNumber) => {
                console.log(`Reconnecting attempt ${attemptNumber}...`);
            });

            newSocket.on('reconnect_failed', () => {
                console.log('Reconnection failed');
                handlers.handleConnectError({ message: 'Reconnection failed after 5 attempts' })
            });
        };

        setupEventListeners();

        return () => {
            console.log('Cleaning up event listeners and disconnecting from server');
            socketRef.current.removeAllListeners();
            socketRef.current.disconnect();
            socketRef.current = null;
        };
    }, [handlers]);

    return {
        emit: (event, data) => {
            if (socketRef.current && socketRef.current.connected) {
                socketRef.current.emit(event, data);
                return true;
            } else {
                console.warn('Socket is not connected. Cannot emit event:', event);
                return false;
            }
        },
        isConnected: () => socketRef.current && socketRef.current.connected,
        id: socketRef.current?.id,
        socket: socketRef.current
    };
};

export default useWebSocket;