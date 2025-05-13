import { useCallback, useEffect, useRef, useState } from 'react';

const useChatMessages = () => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const messagesEndRef = useRef(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    const addMessage = useCallback((text, sender) => {
        setMessages((prev) => [...prev, { text, sender }]);
    }, []);

    useEffect(() => {
        if (messages.length > 0) scrollToBottom();
    }, [messages, scrollToBottom]);

    return {
        messages,
        newMessage,
        setNewMessage,
        addMessage,
        messagesEndRef
    };
};

export default useChatMessages;