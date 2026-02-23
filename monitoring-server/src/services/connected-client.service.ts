import { ConnectedClient, IConnectedClient } from '../database/schemas';
import { logger } from '../utils/logger';

/**
 * Service for managing connected clients
 */
class ConnectedClientService {
  /**
   * Register or update a client connection
   */
  async registerClient(clientId: string, employeeName?: string): Promise<IConnectedClient> {
    try {
      const now = new Date();
      
      const client = await ConnectedClient.findOneAndUpdate(
        { clientId },
        {
          $set: {
            lastSeen: now,
            ...(employeeName && { employeeName }),
          },
          $setOnInsert: {
            clientId,
            firstSeen: now,
          },
        },
        { upsert: true, new: true }
      );

      logger.debug('Client registered/updated', { clientId, employeeName });
      return client;
    } catch (error) {
      logger.error('Error registering client', { error, clientId });
      throw error;
    }
  }

  /**
   * Get all connected clients
   */
  async getAllClients(): Promise<IConnectedClient[]> {
    try {
      return await ConnectedClient.find().sort({ lastSeen: -1 });
    } catch (error) {
      logger.error('Error fetching connected clients', { error });
      throw error;
    }
  }

  /**
   * Get client by ID
   */
  async getClientById(clientId: string): Promise<IConnectedClient | null> {
    try {
      return await ConnectedClient.findOne({ clientId });
    } catch (error) {
      logger.error('Error fetching client', { error, clientId });
      throw error;
    }
  }

  /**
   * Update client employee name
   * Also migrates any existing employee data from client_id to the new employee name
   */
  async updateClientName(clientId: string, employeeName: string): Promise<IConnectedClient | null> {
    try {
      const client = await ConnectedClient.findOneAndUpdate(
        { clientId },
        { $set: { employeeName } },
        { new: true }
      );

      if (!client) {
        logger.warn('Client not found for name update', { clientId });
        return null;
      }

      logger.info('Client name updated', { clientId, employeeName });
      
      // Import Employee model to migrate data
      const { Employee, ActivityLog, Screenshot } = await import('../database/schemas');
      
      // Check if there's an employee record with the client_id as name
      const oldEmployeeRecord = await Employee.findOne({ name: clientId });
      
      if (oldEmployeeRecord) {
        logger.info('Found old employee record with client_id, migrating data', { 
          oldName: clientId, 
          newName: employeeName 
        });
        
        // Check if employee with new name already exists
        let newEmployeeRecord = await Employee.findOne({ name: employeeName });
        
        if (!newEmployeeRecord) {
          // Create new employee record with the employee name
          newEmployeeRecord = await Employee.create({
            name: employeeName,
            location: oldEmployeeRecord.location,
            firstSeen: oldEmployeeRecord.firstSeen,
            lastSeen: oldEmployeeRecord.lastSeen,
          });
          logger.info('Created new employee record', { employeeName });
        } else {
          // Update existing employee record with location if old one has it
          if (oldEmployeeRecord.location && !newEmployeeRecord.location) {
            newEmployeeRecord.location = oldEmployeeRecord.location;
            await newEmployeeRecord.save();
            logger.info('Updated existing employee record with location', { employeeName });
          }
        }
        
        // Migrate activity logs
        const activityLogUpdateResult = await ActivityLog.updateMany(
          { employeeId: oldEmployeeRecord._id },
          { $set: { employeeId: newEmployeeRecord._id } }
        );
        logger.info('Migrated activity logs', { 
          count: activityLogUpdateResult.modifiedCount,
          from: clientId,
          to: employeeName 
        });
        
        // Migrate screenshots
        const screenshotUpdateResult = await Screenshot.updateMany(
          { employeeId: oldEmployeeRecord._id },
          { $set: { employeeId: newEmployeeRecord._id } }
        );
        logger.info('Migrated screenshots', { 
          count: screenshotUpdateResult.modifiedCount,
          from: clientId,
          to: employeeName 
        });
        
        // Delete old employee record
        await Employee.deleteOne({ _id: oldEmployeeRecord._id });
        logger.info('Deleted old employee record', { oldName: clientId });
      }

      return client;
    } catch (error) {
      logger.error('Error updating client name', { error, clientId });
      throw error;
    }
  }

  /**
   * Delete a client
   */
  async deleteClient(clientId: string): Promise<boolean> {
    try {
      const result = await ConnectedClient.deleteOne({ clientId });
      
      if (result.deletedCount === 0) {
        logger.warn('Client not found for deletion', { clientId });
        return false;
      }

      logger.info('Client deleted', { clientId });
      return true;
    } catch (error) {
      logger.error('Error deleting client', { error, clientId });
      throw error;
    }
  }

  /**
   * Get employee name by client ID
   */
  async getEmployeeNameByClientId(clientId: string): Promise<string | null> {
    try {
      const client = await ConnectedClient.findOne({ clientId });
      return client?.employeeName || null;
    } catch (error) {
      logger.error('Error fetching employee name', { error, clientId });
      throw error;
    }
  }
}

export const connectedClientService = new ConnectedClientService();
