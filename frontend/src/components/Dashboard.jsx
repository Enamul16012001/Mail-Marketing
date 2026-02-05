import { useState, useEffect } from 'react';
import {
  EnvelopeIcon,
  DocumentTextIcon,
  FolderIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { getStats, triggerProcessing, healthCheck } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [health, setHealth] = useState(null);

  const fetchData = async () => {
    try {
      const [statsRes, healthRes] = await Promise.all([
        getStats(),
        healthCheck()
      ]);
      setStats(statsRes.data);
      setHealth(healthRes.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleManualProcess = async () => {
    setProcessing(true);
    try {
      const response = await triggerProcessing();
      alert(`Processed ${response.data.processed_count} emails`);
      fetchData();
    } catch (error) {
      alert('Failed to process emails: ' + error.message);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Processed',
      value: stats?.total_emails_processed || 0,
      icon: EnvelopeIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Auto Replied',
      value: stats?.auto_replied || 0,
      icon: CheckCircleIcon,
      color: 'bg-green-500',
    },
    {
      name: 'RAG Replied',
      value: stats?.rag_replied || 0,
      icon: DocumentTextIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'Pending Manual',
      value: stats?.pending_manual || 0,
      icon: ClockIcon,
      color: 'bg-yellow-500',
    },
    {
      name: 'Drafts Pending',
      value: stats?.drafts_pending || 0,
      icon: DocumentTextIcon,
      color: 'bg-orange-500',
    },
    {
      name: 'Knowledge Files',
      value: stats?.knowledge_files || 0,
      icon: FolderIcon,
      color: 'bg-indigo-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
        <div className="flex items-center flex-wrap gap-2">
          <div className={`h-3 w-3 rounded-full ${health?.polling_active ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            System Status: {health?.status === 'healthy' ? 'Healthy' : 'Unknown'}
            {health?.polling_active && ' • Email Polling Active'}
          </span>
          {health?.initialized && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              Initialized (old emails skipped)
            </span>
          )}
        </div>
        <button
          onClick={handleManualProcess}
          disabled={processing}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-5 w-5 mr-2 ${processing ? 'animate-spin' : ''}`} />
          {processing ? 'Processing...' : 'Check Emails Now'}
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">How It Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-green-50 rounded-lg">
            <h4 className="font-medium text-green-800">Auto Reply</h4>
            <p className="text-sm text-green-600 mt-1">
              Generic messages like "Thank you" are replied instantly
            </p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <h4 className="font-medium text-purple-800">RAG Reply</h4>
            <p className="text-sm text-purple-600 mt-1">
              Questions about products/policies use knowledge base
            </p>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg">
            <h4 className="font-medium text-orange-800">Draft Review</h4>
            <p className="text-sm text-orange-600 mt-1">
              Complex questions generate drafts for your review
            </p>
          </div>
          <div className="p-4 bg-yellow-50 rounded-lg">
            <h4 className="font-medium text-yellow-800">Manual Reply</h4>
            <p className="text-sm text-yellow-600 mt-1">
              Critical issues are flagged for your personal attention
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
