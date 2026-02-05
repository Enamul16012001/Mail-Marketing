import { useState, useEffect, useRef } from 'react';
import {
  FolderIcon,
  DocumentIcon,
  TrashIcon,
  ArrowUpTrayIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { getKnowledgeFiles, uploadKnowledgeFile, deleteKnowledgeFile, searchKnowledge } from '../services/api';

function KnowledgeBase() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const fileInputRef = useRef(null);

  const fetchFiles = async () => {
    try {
      const response = await getKnowledgeFiles();
      setFiles(response.data);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
      alert(`File type not supported. Allowed: ${allowedTypes.join(', ')}`);
      return;
    }

    setUploading(true);
    try {
      await uploadKnowledgeFile(file);
      alert('File uploaded successfully!');
      fetchFiles();
    } catch (error) {
      alert('Failed to upload file: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleDelete = async (fileId, filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"? This will also remove it from the knowledge base.`)) {
      return;
    }

    try {
      await deleteKnowledgeFile(fileId);
      alert('File deleted successfully!');
      fetchFiles();
    } catch (error) {
      alert('Failed to delete file: ' + error.message);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const response = await searchKnowledge(searchQuery);
      setSearchResults(response.data.results);
    } catch (error) {
      alert('Search failed: ' + error.message);
    } finally {
      setSearching(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString();
  };

  const getFileIcon = (type) => {
    return DocumentIcon;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Documents</h2>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <FolderIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 mb-4">
            Upload PDF, DOCX, TXT, or MD files to add to the knowledge base
          </p>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept=".pdf,.docx,.doc,.txt,.md"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current.click()}
            disabled={uploading}
            className="flex items-center mx-auto px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <ArrowUpTrayIcon className="h-5 w-5 mr-2" />
            {uploading ? 'Uploading...' : 'Select File'}
          </button>
        </div>
      </div>

      {/* Search Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Search Knowledge Base</h2>
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search for information..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching || !searchQuery.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {searchResults && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Search Results:</h3>
            <p className="text-sm text-gray-600 whitespace-pre-wrap">{searchResults}</p>
          </div>
        )}
      </div>

      {/* Files List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            Knowledge Base Files ({files.length})
          </h2>
        </div>

        {files.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FolderIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No files uploaded yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {files.map((file) => {
              const FileIcon = getFileIcon(file.file_type);
              return (
                <div
                  key={file.id}
                  className="p-4 flex items-center justify-between hover:bg-gray-50"
                >
                  <div className="flex items-center">
                    <FileIcon className="h-10 w-10 text-blue-500 mr-4" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {file.filename}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.file_size)} • {file.chunk_count} chunks •
                        Uploaded {formatDate(file.uploaded_at)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(file.id, file.filename)}
                    className="p-2 text-gray-400 hover:text-red-500"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default KnowledgeBase;
