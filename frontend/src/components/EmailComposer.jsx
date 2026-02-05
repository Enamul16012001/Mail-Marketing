import { useState } from 'react';
import {
  PaperAirplaneIcon,
  XMarkIcon,
  PlusIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { composeEmail } from '../services/api';

// Moved outside to prevent re-creation on every render
function RecipientField({ label, field, emails, onUpdate, onAdd, onRemove }) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      {(emails.length > 0 ? emails : ['']).map((email, index) => (
        <div key={`${field}-${index}`} className="flex items-center gap-2">
          <input
            type="email"
            value={email}
            onChange={(e) => onUpdate(field, index, e.target.value)}
            placeholder="email@example.com"
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
          {emails.length > 1 || field !== 'to' ? (
            <button
              type="button"
              onClick={() => onRemove(field, index)}
              className="p-2 text-gray-400 hover:text-red-500"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          ) : null}
        </div>
      ))}
      <button
        type="button"
        onClick={() => onAdd(field)}
        className="flex items-center text-sm text-blue-600 hover:text-blue-700"
      >
        <PlusIcon className="h-4 w-4 mr-1" />
        Add another
      </button>
    </div>
  );
}

function EmailComposer() {
  const [formData, setFormData] = useState({
    to: [''],
    cc: [],
    bcc: [],
    subject: '',
    body: '',
  });
  const [showCcBcc, setShowCcBcc] = useState(false);
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const addRecipient = (field) => {
    setFormData((prev) => ({
      ...prev,
      [field]: [...prev[field], ''],
    }));
  };

  const removeRecipient = (field, index) => {
    setFormData((prev) => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index),
    }));
  };

  const updateRecipient = (field, index, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: prev[field].map((item, i) => (i === index ? value : item)),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Filter out empty recipients
    const payload = {
      to: formData.to.filter((email) => email.trim()),
      cc: formData.cc.filter((email) => email.trim()),
      bcc: formData.bcc.filter((email) => email.trim()),
      subject: formData.subject,
      body: formData.body,
    };

    if (payload.to.length === 0) {
      setError('At least one recipient is required');
      return;
    }

    if (!payload.body.trim()) {
      setError('Email body is required');
      return;
    }

    setSending(true);

    try {
      await composeEmail(payload);
      setSuccess(`Email sent successfully to ${payload.to.join(', ')}`);
      // Reset form
      setFormData({
        to: [''],
        cc: [],
        bcc: [],
        subject: '',
        body: '',
      });
      setShowCcBcc(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send email');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Compose Email</h2>
        <p className="text-sm text-gray-500">Send a new email to one or multiple recipients</p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* Success/Error Messages */}
        {success && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-700">{success}</p>
          </div>
        )}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* To Field */}
        <RecipientField
          label="To"
          field="to"
          emails={formData.to}
          onUpdate={updateRecipient}
          onAdd={addRecipient}
          onRemove={removeRecipient}
        />

        {/* CC/BCC Toggle */}
        <button
          type="button"
          onClick={() => {
            if (!showCcBcc) {
              setFormData((prev) => ({
                ...prev,
                cc: prev.cc.length > 0 ? prev.cc : [''],
                bcc: prev.bcc.length > 0 ? prev.bcc : [''],
              }));
            }
            setShowCcBcc(!showCcBcc);
          }}
          className="flex items-center text-sm text-gray-600 hover:text-gray-800"
        >
          {showCcBcc ? (
            <ChevronUpIcon className="h-4 w-4 mr-1" />
          ) : (
            <ChevronDownIcon className="h-4 w-4 mr-1" />
          )}
          {showCcBcc ? 'Hide CC/BCC' : 'Add CC/BCC'}
        </button>

        {/* CC/BCC Fields */}
        {showCcBcc && (
          <div className="space-y-4 pl-4 border-l-2 border-gray-200">
            <RecipientField
              label="CC (Carbon Copy)"
              field="cc"
              emails={formData.cc}
              onUpdate={updateRecipient}
              onAdd={addRecipient}
              onRemove={removeRecipient}
            />
            <RecipientField
              label="BCC (Blind Carbon Copy)"
              field="bcc"
              emails={formData.bcc}
              onUpdate={updateRecipient}
              onAdd={addRecipient}
              onRemove={removeRecipient}
            />
          </div>
        )}

        {/* Subject */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Subject
          </label>
          <input
            type="text"
            value={formData.subject}
            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
            placeholder="Email subject"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Body */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Message
          </label>
          <textarea
            value={formData.body}
            onChange={(e) => setFormData({ ...formData, body: e.target.value })}
            placeholder="Write your message here..."
            rows={10}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={sending}
            className={`
              flex items-center px-6 py-2 rounded-md text-white font-medium
              ${sending
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
              }
            `}
          >
            {sending ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Sending...
              </>
            ) : (
              <>
                <PaperAirplaneIcon className="h-5 w-5 mr-2" />
                Send Email
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default EmailComposer;
