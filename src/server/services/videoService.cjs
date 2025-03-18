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
                } else if (data.type === 'video-frame') {
                    framesReceived++;
                    for (const client of clients) {
                        if (client.type === 'python' && client.protocol === 'ws') {
                            client.socket.send(JSON.stringify({ type: 'video', frame: data.frame }));
                            framesForwarded++;
                        }
                    }
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        });
        ws.on('close', () => {
            for (const client of clients) {
                if (client.socket === ws) {
                    clients.delete(client);
                    break;
                }
            }
            console.log('WebSocket client disconnected');
        });
    });

    server.on('upgrade', (request, socket, head) => {
        const pathname = new URL(request.url, 'http://localhost').pathname;

        if (pathname === '/video-ws') {
            wss.handleUpgrade(request, socket, head, (ws) => {
                wss.emit('connection', ws, request);
            });
        }
    });

    // setInterval(() => {
    //     console.log(`Video stats: ${framesReceived} frames received, ${framesForwarded} frames forwarded`);
    //     framesReceived = 0;
    //     framesForwarded = 0;
    // }, 10000);

    return { clients };
}

module.exports = { startVideoService };