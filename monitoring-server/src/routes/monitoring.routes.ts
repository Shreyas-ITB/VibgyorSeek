import { Router } from 'express';
import { logger } from '../utils/logger';
import { validateClientToken } from '../middleware/auth.middleware';
import { validationService } from '../services/validation.service';
import { MonitoringPayload } from '../models/activity-log.model';
import { websocketService } from '../services/websocket.service';
import { dataStorageService } from '../services/data-storage.service';
import { connectedClientService } from '../services/connected-client.service';

const router = Router();

/**
 * POST /api/monitoring/data
 * Receives monitoring data from client applications
 * Validates: Requirements 9.1, 9.2, 9.5
 */
router.post('/data', validateClientToken, async (req, res) => {
  try {
    const payload = req.body;
    
    // Extract client_id from payload
    const clientId = payload?.client_id;
    
    if (!clientId || typeof clientId !== 'string') {
      logger.warn('Missing or invalid client_id in payload', { ip: req.ip });
      res.status(400).json({
        error: 'client_id is required',
      });
      return;
    }
    
    // Register/update client connection
    await connectedClientService.registerClient(clientId);
    
    // Get employee name for this client (if set)
    const employeeName = await connectedClientService.getEmployeeNameByClientId(clientId);
    
    // If no employee name is set, use client_id as fallback for display
    const displayName = employeeName || clientId;
    
    // Validate payload structure (Property 12: Payload Validation)
    const validationResult = validationService.validatePayloadDetailed(payload);
    
    if (!validationResult.valid) {
      // Property 15: Invalid Payload Rejection
      logger.warn('Invalid payload received', {
        errors: validationResult.errors,
        client_id: clientId,
        ip: req.ip
      });
      
      res.status(400).json({
        error: 'Invalid payload structure',
        details: validationResult.errors
      });
      return;
    }
    
    // Type assertion after validation
    const monitoringPayload = payload as MonitoringPayload;
    
    // Override employee_name with the one from connected_clients or use client_id
    monitoringPayload.employee_name = displayName;
    
    logger.info('Processing monitoring data', {
      client_id: clientId,
      employee: displayName,
      timestamp: monitoringPayload.timestamp
    });
    
    // Store data using transaction for consistency (Requirements 17.1, 17.2, 17.4)
    const storageResult = await dataStorageService.storeMonitoringData(monitoringPayload);
    logger.debug('Data stored successfully', storageResult);
    
    // Broadcast notification to dashboard clients (Requirement 15.1)
    // Send employee-specific notification about new monitoring data
    try {
      websocketService.notifyEmployeeUpdate(
        displayName,
        'data_update',
        {
          timestamp: monitoringPayload.timestamp,
          work_seconds: monitoringPayload.activity.work_seconds,
          idle_seconds: monitoringPayload.activity.idle_seconds,
          applications_count: monitoringPayload.applications?.length || 0,
          browser_tabs_count: monitoringPayload.browser_tabs?.length || 0
        }
      );
    } catch (wsError) {
      // Log WebSocket notification error but don't fail the request
      logger.error('Failed to send WebSocket notification', {
        error: wsError instanceof Error ? wsError.message : 'Unknown error',
        employee: displayName
      });
    }
    
    res.status(200).json({
      success: true,
      message: 'Monitoring data received successfully'
    });
    
  } catch (error) {
    logger.error('Error processing monitoring data:', error);
    res.status(500).json({ error: 'Failed to process monitoring data' });
  }
});

export default router;
