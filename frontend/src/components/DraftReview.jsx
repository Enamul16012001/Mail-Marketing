import { useState, useEffect } from 'react';
import {
  DocumentTextIcon,
  CheckIcon,
  XMarkIcon,
  PencilIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { getPendingDrafts, approveDraft, editDraft, discardDraft } from '../services/api';

function DraftReview() {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [processing, setProcessing] = useState(false);

  const fetchDrafts = async () => {
    try {
      const response = await getPendingDrafts();
      setDrafts(response.data);
    } catch (error) {
      console.error('Failed to fetch drafts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrafts();
  }, []);

  const handleSelectDraft = (draft) => {
    setSelectedDraft(draft);
    setEditedContent(draft.ai_response);
    setEditMode(false);
  };

  const handleApprove = async () => {
    if (!selectedDraft) return;

    setProcessing(true);
    try {
      // If edited, save first
      if (editMode && editedContent !== selectedDraft.ai_response) {
        await editDraft(selectedDraft.id, editedContent);
      }
      await approveDraft(selectedDraft.id);
      alert('Draft approved and sent!');
      setSelectedDraft(null);
      fetchDrafts();
    } catch (error) {
      alert('Failed to approve draft: ' + error.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleDiscard = async () => {
    if (!selectedDraft) return;
    if (!confirm('Are you sure you want to discard this draft? The email will be moved back to pending.')) return;

    setProcessing(true);
    try {
      await discardDraft(selectedDraft.id);
      alert('Draft discarded');
      setSelectedDraft(null);
      fetchDrafts();
    } catch (error) {
      alert('Failed to discard draft: ' + error.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedDraft) return;

    setProcessing(true);
    try {
      await editDraft(selectedDraft.id, editedContent);
      alert('Draft updated!');
      setEditMode(false);
      // Update local state
      setSelectedDraft({ ...selectedDraft, ai_response: editedContent });
      fetchDrafts();
    } catch (error) {
      alert('Failed to update draft: ' + error.message);
    } finally {
      setProcessing(false);
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
      {/* Draft List */}
      <div className="w-1/3 bg-white rounded-lg shadow overflow-hidden flex flex-col">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">
            Drafts for Review ({drafts.length})
          </h2>
          <button
            onClick={fetchDrafts}
            className="p-2 text-gray-500 hover:text-gray-700"
          >
            <ArrowPathIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {drafts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No drafts pending review</p>
            </div>
          ) : (
            drafts.map((draft) => (
              <div
                key={draft.id}
                onClick={() => handleSelectDraft(draft)}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  selectedDraft?.id === draft.id ? 'bg-orange-50' : ''
                }`}
              >
                <p className="text-sm font-medium text-gray-900 truncate">
                  {draft.original_email.sender_name || draft.original_email.sender}
                </p>
                <p className="text-sm text-gray-600 truncate">
                  {draft.original_email.subject}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Draft created: {formatDate(draft.created_at)}
                </p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Draft Detail & Review */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
        {selectedDraft ? (
          <>
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Re: {selectedDraft.original_email.subject}
              </h3>
              <p className="text-sm text-gray-600">
                To: {selectedDraft.original_email.sender}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Original Message */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Original Message:</h4>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  {selectedDraft.original_email.body}
                </p>
              </div>

              {/* AI Generated Response */}
              <div className="bg-orange-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-sm font-medium text-orange-800">AI Generated Response:</h4>
                  <button
                    onClick={() => setEditMode(!editMode)}
                    className="flex items-center text-sm text-orange-600 hover:text-orange-800"
                  >
                    <PencilIcon className="h-4 w-4 mr-1" />
                    {editMode ? 'Cancel Edit' : 'Edit'}
                  </button>
                </div>
                {editMode ? (
                  <div>
                    <textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full h-48 p-3 border border-orange-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-orange-500"
                    />
                    <button
                      onClick={handleSaveEdit}
                      disabled={processing}
                      className="mt-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
                    >
                      {processing ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-orange-700 whitespace-pre-wrap">
                    {selectedDraft.ai_response}
                  </p>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={handleDiscard}
                disabled={processing}
                className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                <XMarkIcon className="h-5 w-5 mr-2" />
                Discard
              </button>
              <button
                onClick={handleApprove}
                disabled={processing}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                <CheckIcon className="h-5 w-5 mr-2" />
                {processing ? 'Sending...' : 'Approve & Send'}
              </button>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p>Select a draft to review</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DraftReview;
