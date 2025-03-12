import PropTypes from 'prop-types';
import React, { useEffect, useRef } from 'react';

const ChatWindow = ({ messages, newMessage, onMessageSend, onInputChange, children }) => {

    const lastMessageRef = useRef(null);
    const messagesContainerRef = useRef(null);

    useEffect(() => {
        if (messages.length > 0) {
            lastMessageRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages.length]);
    return (
        <div className="chat-container visible">
            <div className="messages-container" ref={messagesContainerRef} style={{ paddingBottom: '30px' }}>
                <div className="messages-wrapper">
                    <div className="messages-spacer"></div>
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`message ${message.sender}`}
                            ref={index === messages.length - 1 ?
                                lastMessageRef : null}
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
    children: PropTypes.node
};

export default ChatWindow;