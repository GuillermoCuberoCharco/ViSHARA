import PropTypes from 'prop-types';
import React from 'react';

const ChatWindow = ({ messages, newMessage, onMessageSend, onInputChange, children, messagesContainerRef }) => {
    return (
        <div className="chat-container visible">
            <div className="messages-container" ref={messagesContainerRef}>
                <div className="messages-wrapper">
                    <div className="messages-spacer"></div>
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
                    placeholder="Escribe tu mensaje aquí..."
                />
                <button onClick={onMessageSend}>Enviar</button>
            </div>
            {children && (
                <div className="chat-controls-container">
                    {children}
                </div>
            )}
        </div>
    );
};

ChatWindow.propTypes = {
    messages: PropTypes.arrayOf(PropTypes.shape({
        text: PropTypes.string,
        sender: PropTypes.string
    })).isRequired,
    newMessage: PropTypes.string.isRequired,
    onMessageSend: PropTypes.func.isRequired,
    onInputChange: PropTypes.func.isRequired,
    children: PropTypes.node,
    messagesContainerRef: PropTypes.object
};

export default ChatWindow;