import PropTypes from 'prop-types';
import React from 'react';

const ChatWindow = ({ messages, newMessage, onMessageSend, onInputChange }) => (
    <div className="chat-container visible">
        <div className="messages-container">
            <div className="messages-wrapper">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`message ${message.sender}`}
                    >
                        {message.text}
                    </div>
                ))}
            </div>
        </div>
        <div className="input-container">
            <textarea
                value={newMessage}
                onChange={onInputChange}
                onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        onMessageSend();
                    }
                }}
                className="input-field"
            />
        </div>
    </div>
);

ChatWindow.propTypes = {
    messages: PropTypes.arrayOf(PropTypes.shape({
        text: PropTypes.string,
        sender: PropTypes.string
    })).isRequired,
    newMessage: PropTypes.string.isRequired,
    onMessageSend: PropTypes.func.isRequired,
    onInputChange: PropTypes.func.isRequired
};

export default ChatWindow;