import { useState, useEffect } from 'react';
import {
  EnvelopeOpenIcon,
  PaperAirplaneIcon,
  XMarkIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  CodeBracketIcon,
} from '@heroicons/react/24/outline';
import { getPendingEmails, replyToEmail, dismissEmail, searchEmails, bulkDismiss, bulkReply } from '../services/api';

function EmailList() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [showHtml, setShowHtml] = useState(false);

  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showBulkReply, setShowBulkReply] = useState(false);
  const [bulkReplyText, setBulkReplyText] = useState('');
  const [bulkSending, setBulkSending] = useState(false);

  const fetchEmails = async () => {
    try {
      const response = await getPendingEmails();
      setEmails(response.data);
      setSelectedIds(new Set());
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchEmails();
      return;
    }
    setIsSearching(true);
    try {
      const res = await searchEmails(searchQuery, 'pending');
      setEmails(res.data.results || []);
      setSelectedIds(new Set());
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectEmail = (email) => {
    setSelectedEmail(email);
    setReplyText('');
    setShowHtml(false);
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

  // ── Bulk Actions ────────────────────────────────────────────────

  const toggleSelect = (emailId) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(emailId)) {
        next.delete(emailId);
      } else {
        next.add(emailId);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === emails.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(emails.map((e) => e.id)));
    }
  };

  const handleBulkDismiss = async () => {
    if (!confirm(`Dismiss ${selectedIds.size} emails?`)) return;
    try {
      await bulkDismiss(Array.from(selectedIds));
      fetchEmails();
    } catch (error) {
      alert('Bulk dismiss failed: ' + error.message);
    }
  };

  const handleBulkReply = async () => {
    if (!bulkReplyText.trim()) return;
    setBulkSending(true);
    try {
      const res = await bulkReply(Array.from(selectedIds), bulkReplyText);
      alert(`Sent ${res.data.sent} replies (${res.data.failed} failed)`);
      setShowBulkReply(false);
      setBulkReplyText('');
      fetchEmails();
    } catch (error) {
      alert('Bulk reply failed: ' + error.message);
    } finally {
      setBulkSending(false);
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
        <div className="p-4 border-b border-gray-200">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-medium text-gray-900">
              Pending Emails ({emails.length})
            </h2>
            <button
              onClick={() => { setSearchQuery(''); fetchEmails(); }}
              className="p-2 text-gray-500 hover:text-gray-700"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Search Bar */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <MagnifyingGlassIcon className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search pending emails..."
                className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
            >
              {isSearching ? '...' : 'Search'}
            </button>
          </div>
        </div>

        {/* Bulk Action Bar */}
        {selectedIds.size > 0 && (
          <div className="p-3 bg-blue-50 border-b border-blue-100 flex items-center justify-between">
            <span className="text-sm text-blue-700 font-medium">
              {selectedIds.size} selected
            </span>
            <div className="flex gap-2">
              <button
                onClick={handleBulkDismiss}
                className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
              >
                Dismiss
              </button>
              <button
                onClick={() => setShowBulkReply(true)}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                Reply All
              </button>
            </div>
          </div>
        )}

        {/* Select All */}
        {emails.length > 0 && (
          <div className="px-4 py-2 border-b border-gray-100 bg-gray-50">
            <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedIds.size === emails.length && emails.length > 0}
                onChange={toggleSelectAll}
                className="h-3.5 w-3.5 rounded text-blue-600"
              />
              Select All
            </label>
          </div>
        )}

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
                <div className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(email.id)}
                    onChange={(e) => { e.stopPropagation(); toggleSelect(email.id); }}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-1 h-3.5 w-3.5 rounded text-blue-600"
                  />
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
        {showBulkReply ? (
          /* Bulk Reply Panel */
          <div className="flex-1 flex flex-col p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Reply to {selectedIds.size} Emails
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              The same reply will be sent to all selected emails.
            </p>
            <textarea
              value={bulkReplyText}
              onChange={(e) => setBulkReplyText(e.target.value)}
              placeholder="Type your reply..."
              className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => { setShowBulkReply(false); setBulkReplyText(''); }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkReply}
                disabled={!bulkReplyText.trim() || bulkSending}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <PaperAirplaneIcon className="h-5 w-5 mr-2" />
                {bulkSending ? 'Sending...' : `Send to ${selectedIds.size} emails`}
              </button>
            </div>
          </div>
        ) : selectedEmail ? (
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
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-700">Original Message:</h4>
                  {selectedEmail.body_html && (
                    <button
                      onClick={() => setShowHtml(!showHtml)}
                      className={`flex items-center gap-1 px-2 py-1 text-xs rounded ${
                        showHtml ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      <CodeBracketIcon className="h-3 w-3" />
                      {showHtml ? 'HTML' : 'Text'}
                    </button>
                  )}
                </div>
                {showHtml && selectedEmail.body_html ? (
                  <iframe
                    srcDoc={selectedEmail.body_html}
                    sandbox=""
                    className="w-full h-64 border rounded bg-white"
                    title="Email HTML content"
                  />
                ) : (
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">
                    {selectedEmail.body}
                  </p>
                )}
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
