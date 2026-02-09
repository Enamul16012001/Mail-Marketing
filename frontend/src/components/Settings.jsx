import { useState, useEffect } from 'react';
import {
  TrashIcon,
  PlusIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import {
  getSettings, updateSettings,
  getBlocklist, addBlocklistRule, removeBlocklistRule, testBlocklist,
  getRetryQueue, manualRetry, cancelRetry,
} from '../services/api';

function Settings() {
  const [activeSection, setActiveSection] = useState('general');

  const sections = [
    { id: 'general', label: 'General' },
    { id: 'blocklist', label: 'Sender Blocklist' },
    { id: 'retry', label: 'Retry Queue' },
  ];

  return (
    <div className="space-y-6">
      {/* Section Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`px-6 py-3 text-sm font-medium border-b-2 ${
                  activeSection === section.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {section.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeSection === 'general' && <GeneralSettings />}
          {activeSection === 'blocklist' && <BlocklistSettings />}
          {activeSection === 'retry' && <RetryQueueSection />}
        </div>
      </div>
    </div>
  );
}

// ── General Settings ──────────────────────────────────────────────

function GeneralSettings() {
  const [settings, setSettingsState] = useState({ polling_interval: 3, auto_reply_enabled: true });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    getSettings()
      .then((res) => setSettingsState(res.data))
      .catch((err) => console.error('Failed to load settings:', err));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSettings(settings);
      setMessage('Settings saved successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-lg">
      <h3 className="text-lg font-medium text-gray-900">General Settings</h3>

      {message && (
        <div className={`p-3 rounded-lg text-sm ${
          message.includes('Failed') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
        }`}>
          {message}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Polling Interval (minutes)
        </label>
        <input
          type="number"
          min="1"
          max="60"
          value={settings.polling_interval}
          onChange={(e) => setSettingsState({ ...settings, polling_interval: parseInt(e.target.value) || 3 })}
          className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="autoReply"
          checked={settings.auto_reply_enabled}
          onChange={(e) => setSettingsState({ ...settings, auto_reply_enabled: e.target.checked })}
          className="h-4 w-4 text-blue-600 rounded"
        />
        <label htmlFor="autoReply" className="text-sm text-gray-700">
          Enable automatic email replies
        </label>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? 'Saving...' : 'Save Settings'}
      </button>
    </div>
  );
}

// ── Blocklist Settings ────────────────────────────────────────────

function BlocklistSettings() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newRule, setNewRule] = useState({ type: 'exact', value: '', label: '' });
  const [testEmail, setTestEmail] = useState('');
  const [testResult, setTestResult] = useState(null);

  const fetchRules = async () => {
    try {
      const res = await getBlocklist();
      setRules(res.data.rules || []);
    } catch (err) {
      console.error('Failed to load blocklist:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRules(); }, []);

  const handleAdd = async () => {
    if (!newRule.value.trim()) return;
    try {
      const res = await addBlocklistRule(newRule.type, newRule.value, newRule.label);
      setRules(res.data.rules || []);
      setNewRule({ type: 'exact', value: '', label: '' });
    } catch (err) {
      alert('Failed to add rule: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRemove = async (index) => {
    try {
      const res = await removeBlocklistRule(index);
      setRules(res.data.rules || []);
    } catch (err) {
      alert('Failed to remove rule');
    }
  };

  const handleTest = async () => {
    if (!testEmail.trim()) return;
    try {
      const res = await testBlocklist(testEmail);
      setTestResult(res.data);
    } catch (err) {
      alert('Test failed');
    }
  };

  if (loading) {
    return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Sender Blocklist</h3>
        <span className="text-sm text-gray-500">{rules.length} rules</span>
      </div>

      <p className="text-sm text-gray-600">
        Emails from blocked senders will be automatically skipped without classification or reply.
      </p>

      {/* Add Rule Form */}
      <div className="bg-gray-50 rounded-lg p-4 space-y-3">
        <p className="text-sm font-medium text-gray-700">Add New Rule</p>
        <div className="flex gap-3 flex-wrap">
          <select
            value={newRule.type}
            onChange={(e) => setNewRule({ ...newRule, type: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="exact">Exact Email</option>
            <option value="domain">Domain</option>
            <option value="regex">Regex</option>
          </select>
          <input
            type="text"
            value={newRule.value}
            onChange={(e) => setNewRule({ ...newRule, value: e.target.value })}
            placeholder={
              newRule.type === 'exact' ? 'noreply@example.com'
              : newRule.type === 'domain' ? '@newsletter.com'
              : '^noreply@'
            }
            className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            value={newRule.label}
            onChange={(e) => setNewRule({ ...newRule, label: e.target.value })}
            placeholder="Label (optional)"
            className="w-40 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleAdd}
            disabled={!newRule.value.trim()}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            <PlusIcon className="h-4 w-4 mr-1" />
            Add
          </button>
        </div>
      </div>

      {/* Rules Table */}
      <div className="border rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Label</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Action</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rules.map((rule, index) => (
              <tr key={index}>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    rule.type === 'exact' ? 'bg-blue-100 text-blue-800'
                    : rule.type === 'domain' ? 'bg-purple-100 text-purple-800'
                    : 'bg-orange-100 text-orange-800'
                  }`}>
                    {rule.type}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 font-mono">{rule.value}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{rule.label || '-'}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleRemove(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
            {rules.length === 0 && (
              <tr>
                <td colSpan="4" className="px-4 py-8 text-center text-gray-400">
                  No blocklist rules configured
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Test Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Test an Email Address</p>
        <div className="flex gap-3">
          <input
            type="email"
            value={testEmail}
            onChange={(e) => { setTestEmail(e.target.value); setTestResult(null); }}
            placeholder="test@example.com"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyDown={(e) => e.key === 'Enter' && handleTest()}
          />
          <button
            onClick={handleTest}
            disabled={!testEmail.trim()}
            className="flex items-center px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 text-sm"
          >
            <ShieldCheckIcon className="h-4 w-4 mr-1" />
            Test
          </button>
        </div>
        {testResult && (
          <div className={`mt-3 p-2 rounded text-sm ${
            testResult.blocked ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
          }`}>
            {testResult.email}: {testResult.blocked ? 'BLOCKED' : 'ALLOWED'}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Retry Queue Section ───────────────────────────────────────────

function RetryQueueSection() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    try {
      const res = await getRetryQueue();
      setItems(res.data.items || []);
    } catch (err) {
      console.error('Failed to load retry queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleRetry = async (id) => {
    try {
      await manualRetry(id);
      fetchQueue();
    } catch (err) {
      alert('Failed to trigger retry');
    }
  };

  const handleCancel = async (id) => {
    if (!confirm('Cancel this retry?')) return;
    try {
      await cancelRetry(id);
      fetchQueue();
    } catch (err) {
      alert('Failed to cancel retry');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Retry Queue</h3>
        <button onClick={fetchQueue} className="p-2 text-gray-500 hover:text-gray-700">
          <ArrowPathIcon className="h-5 w-5" />
        </button>
      </div>

      <p className="text-sm text-gray-600">
        Failed email sends are queued here for automatic retry with exponential backoff.
      </p>

      {items.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          No items in the retry queue
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Attempts</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Next Retry</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="px-4 py-3 text-sm">
                    <p className="font-medium text-gray-900">{item.sender || 'Unknown'}</p>
                    <p className="text-gray-500 truncate max-w-[200px]">{item.subject || '-'}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      item.status === 'pending' ? 'bg-yellow-100 text-yellow-800'
                      : item.status === 'succeeded' ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                    }`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {item.attempt_count} / {item.max_attempts}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {formatDate(item.next_retry_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-red-600 truncate max-w-[200px]">
                    {item.error_message || '-'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-2 justify-end">
                      {item.status === 'pending' && (
                        <button
                          onClick={() => handleRetry(item.id)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          Retry Now
                        </button>
                      )}
                      {item.status !== 'succeeded' && (
                        <button
                          onClick={() => handleCancel(item.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Settings;
