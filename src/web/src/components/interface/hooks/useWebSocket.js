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
            transports: ['polling', 'websocket'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000,
            forceNew: true,
            withCredentials: true,
            extraHeaders: {
                'Access-Control-Allow-Origin': '*'
            }
        });

        socketRef.current = newSocket;
        setSocket(newSocket);

        const setupEventListeners = () => {
            newSocket.on('connect', () => {
                console.log('Connected to server');
                newSocket.emit('register_client', 'web');
            });

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
            socketRef.current.offAny();
            socketRef.current.disconnect();
            socketRef.current = null;
        };
    }, [handlers]);

    return socketRef.current;
};

export default useWebSocket;