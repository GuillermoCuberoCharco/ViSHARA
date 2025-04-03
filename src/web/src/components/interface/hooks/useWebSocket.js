import { useEffect, useState } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../../../config";

const useWebSocket = (handlers) => {
    const [websocket, setWebSocket] = useState(null);

    useEffect(() => {
        const socket = io(SERVER_URL, {
            path: '/message-socket',
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000,
            forceNew: true
        });

        setWebSocket(socket);

        const setupEventListeners = () => {
            websocket.on('connect', () => {
                console.log('Connected to server');
                socket.emit('register_client', 'web');
            });

            websocket.on('registration_success', handlers.handleRegistrationSuccess);
            websocket.on('robot_message', handlers.handleRobotMessage);
            websocket.on('wizard_message', handlers.handleWizardMessage);
            websocket.on('client_message', handlers.handleClientMessage);
            websocket.on('connect_error', handlers.handleConnectError);
            websocket.on('error', handlers.handleSocketError);

            websocket.on('reconnect_attempt', (attemptNumber) => {
                console.log(`Reconnecting attempt ${attemptNumber}...`);
            });

            websocket.on('reconnect_failed', () => {
                console.log('Reconnection failed');
                handlers.handleConnectError({ message: 'Reconnection failed after 5 attempts' })
            });
        };

        setupEventListeners();

        return () => {
            websocket.offAny();
            websocket.disconnect();
        };
    }, [handlers]);

    return websocket;
};

export default useWebSocket;