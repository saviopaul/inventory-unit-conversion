import React, { useState } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import SchemaViewer from './components/SchemaViewer';
import ReportBuilder from './components/ReportBuilder';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">GoFrugal Report Builder</h1>
          <p className="text-blue-100 mt-1">Custom Report Builder - No Vendor Fees</p>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'dashboard'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              data-testid="tab-dashboard"
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('schemas')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'schemas'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              data-testid="tab-schemas"
            >
              Schema Viewer
            </button>
            <button
              onClick={() => setActiveTab('builder')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'builder'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              data-testid="tab-builder"
            >
              Report Builder
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'schemas' && <SchemaViewer />}
        {activeTab === 'builder' && <ReportBuilder />}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-300 mt-12">
        <div className="container mx-auto px-4 py-6 text-center">
          <p>© 2025 GoFrugal Report Builder - Built to reduce vendor costs</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
