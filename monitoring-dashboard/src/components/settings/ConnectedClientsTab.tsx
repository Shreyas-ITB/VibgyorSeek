import React, { useState, useEffect } from 'react';
import { Pencil, Trash2, Monitor, RefreshCw } from 'lucide-react';
import api from '../../services/api';

interface ConnectedClient {
  clientId: string;
  employeeName: string | null;
  firstSeen: string;
  lastSeen: string;
}

const ConnectedClientsTab: React.FC = () => {
  const [clients, setClients] = useState<ConnectedClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingClientId, setEditingClientId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchClients = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/connected-clients');
      setClients(response.data.clients);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch connected clients');
      console.error('Error fetching clients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleEditClick = (client: ConnectedClient) => {
    setEditingClientId(client.clientId);
    setEditName(client.employeeName || '');
  };

  const handleSaveName = async (clientId: string) => {
    if (!editName.trim()) {
      alert('Employee name cannot be empty');
      return;
    }

    try {
      await api.put(`/connected-clients/${clientId}/name`, {
        employeeName: editName.trim(),
      });
      
      // Update local state
      setClients(clients.map(c => 
        c.clientId === clientId 
          ? { ...c, employeeName: editName.trim() }
          : c
      ));
      
      setEditingClientId(null);
      setEditName('');
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to update client name');
      console.error('Error updating client name:', err);
    }
  };

  const handleCancelEdit = () => {
    setEditingClientId(null);
    setEditName('');
  };

  const handleDeleteClient = async (clientId: string, employeeName: string | null) => {
    const displayName = employeeName || clientId;
    if (!confirm(`Are you sure you want to delete client "${displayName}"?`)) {
      return;
    }

    try {
      await api.delete(`/connected-clients/${clientId}`);
      
      // Remove from local state
      setClients(clients.filter(c => c.clientId !== clientId));
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to delete client');
      console.error('Error deleting client:', err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Connected Clients
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Manage connected monitoring clients and assign employee names
          </p>
        </div>
        <button
          onClick={fetchClients}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 rounded-lg text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {clients.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Monitor className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            No connected clients found
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Client ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Employee Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  First Seen
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Last Seen
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {clients.map((client) => (
                <tr key={client.clientId} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-gray-300">
                    {client.clientId.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-300">
                    {editingClientId === client.clientId ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          placeholder="Enter employee name"
                          autoFocus
                        />
                        <button
                          onClick={() => handleSaveName(client.clientId)}
                          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-xs"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 text-xs"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <span className={!client.employeeName ? 'text-gray-400 italic' : ''}>
                        {client.employeeName || '(no name)'}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(client.firstSeen)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(client.lastSeen)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {editingClientId !== client.clientId && (
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEditClick(client)}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                          title="Edit employee name"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClient(client.clientId, client.employeeName)}
                          className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                          title="Delete client"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ConnectedClientsTab;
