import { useState, useEffect } from 'react';
import {
  EnvelopeOpenIcon,
  PaperAirplaneIcon,
  XMarkIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { getPendingEmails, replyToEmail, dismissEmail } from '../services/api';

function EmailList() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);

  const fetchEmails = async () => {
    try {
      const response = await getPendingEmails();
      setEmails(response.data);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  const handleSelectEmail = (email) => {
    setSelectedEmail(email);
    setReplyText('');
  };

  const handleSendReply = async () => {
    if (!replyText.trim() || !selectedEmail) return;

    setSending(true);
    try {
      await replyToEmail(selectedEmail.id, replyText);
      alert('Reply sent successfully!');
      setSelectedEmail(null);
      setReplyText('');
      fetchEmails();
    } catch (error) {
      alert('Failed to send reply: ' + error.message);
    } finally {
      setSending(false);
    }
  };

  const handleDismiss = async (emailId) => {
    if (!confirm('Are you sure you want to dismiss this email?')) return;

    try {
      await dismissEmail(emailId);
      fetchEmails();
      if (selectedEmail?.id === emailId) {
        setSelectedEmail(null);
      }
    } catch (error) {
      alert('Failed to dismiss email: ' + error.message);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-240px)]">
      {/* Email List */}
      <div className="w-1/3 bg-white rounded-lg shadow overflow-hidden flex flex-col">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">
            Pending Emails ({emails.length})
          </h2>
          <button
            onClick={fetchEmails}
            className="p-2 text-gray-500 hover:text-gray-700"
          >
            <ArrowPathIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {emails.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <EnvelopeOpenIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No pending emails</p>
            </div>
          ) : (
            emails.map((email) => (
              <div
                key={email.id}
                onClick={() => handleSelectEmail(email)}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  selectedEmail?.id === email.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {email.sender_name || email.sender}
                    </p>
                    <p className="text-sm text-gray-600 truncate">{email.subject}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatDate(email.received_at)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDismiss(email.id);
                    }}
                    className="ml-2 p-1 text-gray-400 hover:text-red-500"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Email Detail & Reply */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
        {selectedEmail ? (
          <>
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                {selectedEmail.subject}
              </h3>
              <p className="text-sm text-gray-600">
                From: {selectedEmail.sender_name || selectedEmail.sender}
              </p>
              <p className="text-xs text-gray-400">
                {formatDate(selectedEmail.received_at)}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Original Message:</h4>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  {selectedEmail.body}
                </p>
              </div>

              {selectedEmail.attachments?.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Attachments:</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedEmail.attachments.map((att, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-gray-100 rounded text-sm text-gray-600"
                      >
                        {att.filename}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-200">
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Type your reply..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex justify-end mt-3">
                <button
                  onClick={handleSendReply}
                  disabled={!replyText.trim() || sending}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <PaperAirplaneIcon className="h-5 w-5 mr-2" />
                  {sending ? 'Sending...' : 'Send Reply'}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <EnvelopeOpenIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p>Select an email to view and reply</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default EmailList;
