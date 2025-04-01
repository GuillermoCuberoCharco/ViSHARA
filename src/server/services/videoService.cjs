const WebSocket = require('ws');

function startVideoService(server) {
    const clients = new Set();
    let framesReceived = 0;
    let framesForwarded = 0;

    const wss = new WebSocket.Server({ noServer: true });

    wss.on('connection', (ws) => {
        console.log('A WebSocket client connected');

        ws.on('message', (message) => {
            try {
                const data = JSON.parse(message);
                if (data.type === 'register') {
                    console.log('WebSocket client registered:', data.clientId);
                    clients.add({ socket: ws, type: data.client, protocol: 'ws' });

                    ws.send(JSON.stringify({ type: 'registration_success', status: 'ok' }));
                } else if (data.type === 'video-frame' || data.data) {
                    framesReceived++;
                    const frameData = data.frame || data.data;
                    for (const client of clients) {
                        if (client.type === 'python' && client.socket.readySate === WebSocket.OPEN) {
                            client.socket.send(JSON.stringify({ type: 'video', frame: frameData }));
                            framesForwarded++;
                        }
                    }
                }

                if (framesReceived % 100 === 0) {
                    console.log(`Video stats: ${framesReceived} frames received, ${framesForwarded} frames forwarded`);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        });
        ws.on('close', () => {
            for (const client of clients) {
                if (client.socket === ws) {
                    clients.delete(client);
                    console.log('WebSocket client disconnected:', client.type || 'unknown');
                    break;
                }
            }
        });

        const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.ping();
            } else {
                clearInterval(pingInterval);
            }
        }, 30000);
    });

    server.on('upgrade', (request, socket, head) => {
        const pathname = new URL(request.url, 'http://localhost').pathname;

        if (pathname === '/video-socket') {
            wss.handleUpgrade(request, socket, head, (ws) => {
                wss.emit('connection', ws, request);
            });
        }
    });

    return { clients };
}

module.exports = startVideoService;