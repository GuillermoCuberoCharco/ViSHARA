const express = require('express');
const {
    getConversationStats,
    getConversationContext,
    cleanupOldConversations,
    saveConversationsToFile,
    getUserConversationHistory
} = require('../../services/conversationService.cjs');

const router = express.Router();

router.get('/stats', (req, res) => {
    try {
        const stats = getConversationStats();
        res.json({
            success: true,
            data: stats,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error getting conversation stats:', error);
        res.status(500).json({
            success: false,
            error: 'Error retrieving conversation statistics'
        });
    }
});

router.get('/user/:userId/history', (req, res) => {
    try {
        const { userId } = req.params;
        const history = getUserConversationHistory(userId);

        res.json({
            success: true,
            userId: userId,
            data: history,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error getting user conversation history:', error);
        res.status(500).json({
            success: false,
            error: 'Error retrieving user conversation history'
        });
    }
});

router.post('/cleanup', async (req, res) => {
    try {
        const { days = 90 } = req.body;
        const cleanedCount = await cleanupOldConversations(parseInt(days));

        res.json({
            success: true,
            message: `Cleanup completed`,
            sessionsRemoved: cleanedCount,
            daysThreshold: parseInt(days),
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error cleaning up conversations:', error);
        res.status(500).json({
            success: false,
            error: 'Error during conversation cleanup'
        });
    }
});

router.post('/save', async (req, res) => {
    try {
        await saveConversationsToFile();
        res.json({
            success: true,
            message: 'Conversations saved successfully',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error saving conversations:', error);
        res.status(500).json({
            success: false,
            error: 'Error saving conversations'
        });
    }
});

function setupConversationRoutes() {
    return router;
}

module.exports = setupConversationRoutes;