import { useEffect, useState } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../../../config";

const useWebSocket = (handlers) => {
    const [websocket, setWebSocket] = useState(null);

    useEffect(() => {
        const socket = io(SERVER_URL, {
            transport: ['polling', 'websocket']
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