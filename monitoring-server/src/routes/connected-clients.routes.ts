import { Router } from 'express';
import { logger } from '../utils/logger';
import { connectedClientService } from '../services/connected-client.service';

const router = Router();

/**
 * GET /api/connected-clients
 * Get all connected clients
 */
router.get('/', async (req, res) => {
  try {
    const clients = await connectedClientService.getAllClients();
    
    res.status(200).json({
      success: true,
      clients: clients.map(client => ({
        clientId: client.clientId,
        employeeName: client.employeeName || null,
        firstSeen: client.firstSeen,
        lastSeen: client.lastSeen,
      })),
    });
  } catch (error) {
    logger.error('Error fetching connected clients', { error });
    res.status(500).json({ error: 'Failed to fetch connected clients' });
  }
});

/**
 * PUT /api/connected-clients/:clientId/name
 * Update client employee name
 */
router.put('/:clientId/name', async (req, res) => {
  try {
    const { clientId } = req.params;
    const { employeeName } = req.body;

    if (!employeeName || typeof employeeName !== 'string' || !employeeName.trim()) {
      res.status(400).json({ error: 'Valid employee name is required' });
      return;
    }

    const client = await connectedClientService.updateClientName(clientId, employeeName.trim());

    if (!client) {
      res.status(404).json({ error: 'Client not found' });
      return;
    }

    res.status(200).json({
      success: true,
      client: {
        clientId: client.clientId,
        employeeName: client.employeeName,
        firstSeen: client.firstSeen,
        lastSeen: client.lastSeen,
      },
    });
  } catch (error) {
    logger.error('Error updating client name', { error });
    res.status(500).json({ error: 'Failed to update client name' });
  }
});

/**
 * DELETE /api/connected-clients/:clientId
 * Delete a client
 */
router.delete('/:clientId', async (req, res) => {
  try {
    const { clientId } = req.params;

    const deleted = await connectedClientService.deleteClient(clientId);

    if (!deleted) {
      res.status(404).json({ error: 'Client not found' });
      return;
    }

    res.status(200).json({
      success: true,
      message: 'Client deleted successfully',
    });
  } catch (error) {
    logger.error('Error deleting client', { error });
    res.status(500).json({ error: 'Failed to delete client' });
  }
});

export default router;
