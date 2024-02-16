import React, { useState } from 'react';

function SendMessageForm({ socket, onClose }) {
  const [message, setMessage] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(message);
    }
    setMessage('');
    onClose();
  };

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        style={{ width: '100%', height: '70vh', resize: 'none' }}
      />
      <button type="submit">Enviar</button>
    </form>
  );
}

export default SendMessageForm;