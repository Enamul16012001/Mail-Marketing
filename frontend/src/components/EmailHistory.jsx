import { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  EnvelopeIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  CodeBracketIcon,
} from '@heroicons/react/24/outline';
import { getEmailHistory, searchEmails } from '../services/api';

function EmailHistory() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [showHtml, setShowHtml] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await getEmailHistory(100);
      setEmails(response.data);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchHistory();
      return;
    }
    setIsSearching(true);
    try {
      const res = await searchEmails(searchQuery, 'history');
      setEmails(res.data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  const getCategoryBadge = (category) => {
    const badges = {
      auto_reply: { bg: 'bg-green-100', text: 'text-green-800', label: 'Auto Reply' },
      rag_reply: { bg: 'bg-purple-100', text: 'text-purple-800', label: 'RAG Reply' },
      draft_review: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Draft Approved' },
      pending_manual: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Manual Reply' },
    };
    const badge = badges[category] || { bg: 'bg-gray-100', text: 'text-gray-800', label: category };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
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
              Sent Emails ({emails.length})
            </h2>
            <button
              onClick={() => { setSearchQuery(''); fetchHistory(); }}
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
                placeholder="Search email history..."
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

        <div className="flex-1 overflow-y-auto">
          {emails.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <EnvelopeIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No sent emails yet</p>
            </div>
          ) : (
            emails.map((email) => (
              <div
                key={email.id}
                onClick={() => { setSelectedEmail(email); setShowHtml(false); }}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  selectedEmail?.id === email.id ? 'bg-green-50' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-medium text-gray-900 truncate flex-1">
                    {email.sender_name || email.sender}
                  </p>
                  <CheckCircleIcon className="h-4 w-4 text-green-500 ml-2" />
                </div>
                <p className="text-sm text-gray-600 truncate">{email.subject}</p>
                <div className="flex items-center justify-between mt-2">
                  {getCategoryBadge(email.category)}
                  <span className="text-xs text-gray-400">
                    {formatDate(email.processed_at)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Email Detail */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
        {selectedEmail ? (
          <>
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-medium text-gray-900">
                  {selectedEmail.subject}
                </h3>
                {getCategoryBadge(selectedEmail.category)}
              </div>
              <p className="text-sm text-gray-600">
                From: {selectedEmail.sender_name || selectedEmail.sender}
              </p>
              <p className="text-xs text-gray-400">
                Received: {formatDate(selectedEmail.received_at)} •
                Replied: {formatDate(selectedEmail.processed_at)}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Original Message */}
              <div className="bg-gray-50 rounded-lg p-4">
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

              {/* Our Response */}
              {selectedEmail.ai_response && (
                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-green-800 mb-2">Our Response:</h4>
                  <p className="text-sm text-green-700 whitespace-pre-wrap">
                    {selectedEmail.ai_response}
                  </p>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <EnvelopeIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p>Select an email to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default EmailHistory;
