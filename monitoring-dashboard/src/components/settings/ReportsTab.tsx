import React, { useState, useEffect } from 'react';
import { Mail, Send, Plus, Trash2, RefreshCw, CheckCircle, AlertCircle, Eye, EyeOff, TestTube } from 'lucide-react';
import api from '../../services/api';
import toast from 'react-hot-toast';

interface ReportsConfig {
  enabled: boolean;
  recipients: string[];
  schedule: 'weekly' | 'monthly';
  dayOfWeek: number;
  timeOfDay: string;
}

interface SMTPConfig {
  configured: boolean;
  email: string;
  hasPassword: boolean;
}

const ReportsTab: React.FC = () => {
  const [config, setConfig] = useState<ReportsConfig | null>(null);
  const [smtpConfig, setSmtpConfig] = useState<SMTPConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [smtpEmail, setSmtpEmail] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [showSmtpEmail, setShowSmtpEmail] = useState(false);
  const [showSmtpPassword, setShowSmtpPassword] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  const [sendingReport, setSendingReport] = useState(false);

  useEffect(() => {
    fetchConfig();
    fetchSMTPConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const response = await api.get('/reports/config');
      setConfig(response.data);
    } catch (error) {
      console.error('Error fetching reports config:', error);
      toast.error('Failed to fetch reports configuration');
    } finally {
      setLoading(false);
    }
  };

  const fetchSMTPConfig = async () => {
    try {
      const response = await api.get('/reports/smtp-config');
      setSmtpConfig(response.data);
      setSmtpEmail(response.data.email || '');
      // Don't set password - let user enter new one if they want to change it
      setSmtpPassword('');
    } catch (error) {
      console.error('Error fetching SMTP config:', error);
    }
  };

  const handleSaveSMTP = async () => {
    if (!smtpEmail) {
      toast.error('Please enter email address');
      return;
    }

    // If no existing password and no new password provided
    if (!smtpPassword && !smtpConfig?.hasPassword) {
      toast.error('Please enter app password');
      return;
    }

    setSaving(true);
    try {
      const payload: any = { email: smtpEmail };
      
      // Only send password if user entered a new one
      if (smtpPassword) {
        payload.appPassword = smtpPassword;
      }

      await api.put('/reports/smtp-config', payload);
      
      if (smtpPassword) {
        toast.success('SMTP configuration saved successfully!');
      } else {
        toast.success('SMTP email updated successfully!');
      }
      
      setSmtpPassword(''); // Clear password field after saving
      setShowSmtpPassword(false);
      fetchSMTPConfig();
    } catch (error: any) {
      console.error('Error saving SMTP config:', error);
      toast.error(error.response?.data?.error || 'Failed to save SMTP configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleAddRecipient = async () => {
    if (!newEmail) {
      toast.error('Please enter an email address');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newEmail)) {
      toast.error('Please enter a valid email address');
      return;
    }

    try {
      const response = await api.post('/reports/recipients', { email: newEmail });
      setConfig(response.data.config);
      setNewEmail('');
      toast.success('Recipient added successfully!');
    } catch (error: any) {
      console.error('Error adding recipient:', error);
      toast.error(error.response?.data?.error || 'Failed to add recipient');
    }
  };

  const handleRemoveRecipient = async (email: string) => {
    try {
      const response = await api.delete(`/reports/recipients/${encodeURIComponent(email)}`);
      setConfig(response.data.config);
      toast.success('Recipient removed successfully!');
    } catch (error: any) {
      console.error('Error removing recipient:', error);
      toast.error(error.response?.data?.error || 'Failed to remove recipient');
    }
  };

  const handleToggleEnabled = async (enabled: boolean) => {
    if (!config) return;

    try {
      const response = await api.put('/reports/config', { ...config, enabled });
      setConfig(response.data.config);
      toast.success(enabled ? 'Reports enabled!' : 'Reports disabled');
    } catch (error: any) {
      console.error('Error toggling reports:', error);
      toast.error(error.response?.data?.error || 'Failed to update reports status');
    }
  };

  const handleSendTestEmail = async () => {
    if (!newEmail) {
      toast.error('Please enter an email address to send test email');
      return;
    }

    setSendingTest(true);
    try {
      await api.post('/reports/test-email', { email: newEmail });
      toast.success(`Test email sent to ${newEmail}!`);
    } catch (error: any) {
      console.error('Error sending test email:', error);
      toast.error(error.response?.data?.error || 'Failed to send test email');
    } finally {
      setSendingTest(false);
    }
  };

  const handleSendReportNow = async () => {
    if (!config || config.recipients.length === 0) {
      toast.error('Please add at least one recipient');
      return;
    }

    setSendingReport(true);
    try {
      await api.post('/reports/send-now');
      toast.success('Weekly report sent successfully!');
    } catch (error: any) {
      console.error('Error sending report:', error);
      toast.error(error.response?.data?.error || 'Failed to send report');
    } finally {
      setSendingReport(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Weekly Reports & Notifications
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Configure automated weekly productivity reports sent via email
        </p>
      </div>

      {/* SMTP Configuration */}
      <div className="bg-gray-50 dark:bg-gray-700/50 p-6 rounded-lg mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Mail className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          Gmail SMTP Configuration
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Configure Gmail SMTP to send automated reports. You'll need to generate an App Password from your Google Account settings.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Gmail Address
            </label>
            <div className="relative">
              <input
                type={showSmtpEmail ? 'text' : 'password'}
                value={smtpEmail}
                onChange={(e) => setSmtpEmail(e.target.value)}
                placeholder="your-email@gmail.com"
                className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <button
                type="button"
                onClick={() => setShowSmtpEmail(!showSmtpEmail)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showSmtpEmail ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Gmail App Password
              {smtpConfig?.hasPassword && (
                <span className="ml-2 text-xs text-green-600 dark:text-green-400">
                  (Configured ✓)
                </span>
              )}
            </label>
            <div className="relative">
              <input
                type={showSmtpPassword ? 'text' : 'password'}
                value={smtpPassword}
                onChange={(e) => setSmtpPassword(e.target.value)}
                placeholder={smtpConfig?.hasPassword ? "Leave empty to keep existing password, use quotes to cover the app password before saving" : "Enter 16-character app password"}
                className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <button
                type="button"
                onClick={() => setShowSmtpPassword(!showSmtpPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showSmtpPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Generate an App Password at: <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">myaccount.google.com/apppasswords</a>
            </p>
            {smtpConfig?.hasPassword && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                Password is already configured. Enter a new one only if you want to change it.
              </p>
            )}
          </div>

          <button
            onClick={handleSaveSMTP}
            disabled={saving || !smtpEmail}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Save SMTP Configuration
              </>
            )}
          </button>
        </div>
      </div>

      {/* Report Recipients */}
      <div className="bg-gray-50 dark:bg-gray-700/50 p-6 rounded-lg mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Send className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          Report Recipients
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Add up to 5 email addresses to receive weekly productivity reports
        </p>

        {/* Add Recipient */}
        <div className="flex gap-2 mb-4">
          <input
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddRecipient()}
            placeholder="Enter email address"
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <button
            onClick={handleAddRecipient}
            disabled={!newEmail || (config?.recipients.length || 0) >= 5}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="w-4 h-4" />
            Add
          </button>
          <button
            onClick={handleSendTestEmail}
            disabled={sendingTest || !newEmail || !smtpConfig?.configured}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Send test email to verify configuration"
          >
            {sendingTest ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <TestTube className="w-4 h-4" />
            )}
            Test
          </button>
        </div>

        {/* Recipients List */}
        {config && config.recipients.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Recipients ({config.recipients.length}/5):
            </p>
            {config.recipients.map((email) => (
              <div
                key={email}
                className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600"
              >
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-900 dark:text-white">{email}</span>
                </div>
                <button
                  onClick={() => handleRemoveRecipient(email)}
                  className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Mail className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No recipients added yet</p>
          </div>
        )}
      </div>

      {/* Report Settings */}
      {config && (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-6 rounded-lg mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Report Settings
          </h3>

          <div className="space-y-4">
            {/* Enable/Disable Reports */}
            <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">Enable Weekly Reports</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Automatically send reports every Monday at 9:00 AM
                </p>
              </div>
              <button
                onClick={() => handleToggleEnabled(!config.enabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  config.enabled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    config.enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Send Report Now */}
            <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">Send Report Now</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Send a weekly report immediately to all recipients
                </p>
              </div>
              <button
                onClick={handleSendReportNow}
                disabled={sendingReport || config.recipients.length === 0 || !smtpConfig?.configured}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sendingReport ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send Now
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-1">About Weekly Reports</p>
            <p>
              Reports include productivity insights, top performers, idle time analysis, and application usage statistics for all employees. 
              Reports are automatically generated from the past 7 days of activity data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsTab;
