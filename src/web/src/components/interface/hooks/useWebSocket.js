import { useEffect, useState } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../../../config";

const useWebSocket = (handlers) => {
    const [websocket, setWebSocket] = useState(null);

    useEffect(() => {
        const socket = io(SERVER_URL, {
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000,
            forceNew: true
        });

        setWebSocket(socket);

        const setupEventListeners = () => {
            socket.on('connect', () => {
                console.log('Connected to server');
                socket.emit('register_client', 'web');
            });

            socket.on('registration_success', handlers.handleRegistrationSuccess);
            socket.on('robot_message', handlers.handleRobotMessage);
            socket.on('wizard_message', handlers.handleWizardMessage);
            socket.on('client_message', handlers.handleClientMessage);
            socket.on('connect_error', handlers.handleConnectError);
            socket.on('error', handlers.handleSocketError);

            socket.on('reconnect_attempt', (attemptNumber) => {
                console.log(`Reconnecting attempt ${attemptNumber}...`);
            });

            socket.on('reconnect_failed', () => {
                console.log('Reconnection failed');
                handlers.handleConnectError({ message: 'Reconnection failed after 5 attempts' })
            });
        };

        setupEventListeners();

        return () => {
            socket.offAny();
            socket.disconnect();
        };
    }, [handlers]);

    return websocket;
};

export default useWebSocket;