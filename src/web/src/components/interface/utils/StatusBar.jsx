import React from "react";
import '../styles/StatusBar.css';

const StatusBar = ({
    isRecording,
    isWaiting,
    isWaitingResponse,
    audioSrc,
    connectionError,
    isRegistered
}) => {
    const getStatusMessage = () => {
        if (connectionError) {
            return {
                message: "Connection error",
                icon: "⚠️",
                bgColor: "status-bar-error"
            };
        }

        if (!isRegistered) {
            return {
                message: "Connecting to the server...",
                icon: "🔄",
                bgColor: "status-bar-connecting"
            };
        }

        if (isRecording) {
            return {
                message: "Recording audio...",
                icon: "🎙️",
                bgColor: "status-bar-recording"
            };
        }

        if (isWaiting) {
            return {
                message: "Processing audio...",
                icon: "⚙️",
                color: "status-bar-processing"
            };
        }

        if (isWaitingResponse) {
            return {
                message: "Waiting for response...",
                icon: "⏳",
                color: "status-bar-waiting"
            };
        }

        if (audioSrc) {
            return {
                message: "Audio ready",
                icon: "🔊",
                color: "status-bar-playing"
            };
        }

        return {
            message: "Ready",
            icon: "✅",
            color: "status-bar-ready"
        };
    };

    const status = getStatusMessage();

    return (
        <div className={`status-bar ${status.bgColor}`}>
            <span className="status-bar-icon">{status.icon}</span>
            <span className="status-bar-message">{status.message}</span>
        </div>
    );
};

export default StatusBar;