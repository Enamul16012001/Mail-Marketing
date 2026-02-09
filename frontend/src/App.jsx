import { useState } from 'react';
import {
  EnvelopeIcon,
  DocumentTextIcon,
  FolderIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  PencilSquareIcon,
  PresentationChartLineIcon,
} from '@heroicons/react/24/outline';
import Dashboard from './components/Dashboard';
import EmailList from './components/EmailList';
import DraftReview from './components/DraftReview';
import KnowledgeBase from './components/KnowledgeBase';
import EmailHistory from './components/EmailHistory';
import EmailComposer from './components/EmailComposer';
import Analytics from './components/Analytics';
import Settings from './components/Settings';

const navigation = [
  { name: 'Dashboard', icon: ChartBarIcon, id: 'dashboard' },
  { name: 'Analytics', icon: PresentationChartLineIcon, id: 'analytics' },
  { name: 'Compose', icon: PencilSquareIcon, id: 'compose' },
  { name: 'Pending Emails', icon: EnvelopeIcon, id: 'pending' },
  { name: 'Draft Review', icon: DocumentTextIcon, id: 'drafts' },
  { name: 'Knowledge Base', icon: FolderIcon, id: 'knowledge' },
  { name: 'Email History', icon: Cog6ToothIcon, id: 'history' },
  { name: 'Settings', icon: Cog6ToothIcon, id: 'settings' },
];

function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'analytics':
        return <Analytics />;
      case 'compose':
        return <EmailComposer />;
      case 'pending':
        return <EmailList />;
      case 'drafts':
        return <DraftReview />;
      case 'knowledge':
        return <KnowledgeBase />;
      case 'history':
        return <EmailHistory />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <EnvelopeIcon className="h-8 w-8 text-blue-600" />
              <h1 className="ml-3 text-xl font-semibold text-gray-900">
                AI Email Auto-Reply
              </h1>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-6 overflow-x-auto">
            {navigation.map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`
                  flex items-center py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                  ${currentTab === item.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <item.icon className="h-5 w-5 mr-2" />
                {item.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <main>
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;
