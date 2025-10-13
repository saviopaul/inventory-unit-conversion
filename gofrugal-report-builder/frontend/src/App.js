import React, { useState, useEffect } from 'react';
import './App.css';
import ReportBrowser from './components/ReportBrowser';
import ReportBuilder from './components/ReportBuilder';
import ChatInterface from './components/ChatInterface';

function App() {
  const [currentView, setCurrentView] = useState('browser'); // browser, builder, preview
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);

  const API_URL = 'http://localhost:8002';

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch(`${API_URL}/api/reports`);
      const data = await response.json();
      setReports(data.reports);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setLoading(false);
    }
  };

  const handleViewReport = (reportId) => {
    setSelectedReport(reportId);
    setCurrentView('builder');
  };

  return (
    <div className="App">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>🎯 GoFrugal Report Builder</h1>
          <div className="header-stats">
            <span className="stat-badge">{reports.length} Reports</span>
            <span className="stat-badge">AI-Powered</span>
          </div>
        </div>
        <nav className="header-nav">
          <button 
            className={`nav-btn ${currentView === 'browser' ? 'active' : ''}`}
            onClick={() => setCurrentView('browser')}
          >
            📊 Browse Reports
          </button>
          <button 
            className={`nav-btn ${currentView === 'builder' ? 'active' : ''}`}
            onClick={() => setCurrentView('builder')}
          >
            🔨 Build Report
          </button>
          <button 
            className="nav-btn ai-btn"
            onClick={() => setChatOpen(!chatOpen)}
          >
            🤖 AI Assistant {chatOpen && '(Open)'}
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="content-area">
          {loading ? (
            <div className="loading-screen">
              <div className="spinner"></div>
              <p>Loading reports...</p>
            </div>
          ) : (
            <>
              {currentView === 'browser' && (
                <ReportBrowser 
                  reports={reports} 
                  onViewReport={handleViewReport}
                  apiUrl={API_URL}
                />
              )}
              
              {currentView === 'builder' && (
                <ReportBuilder 
                  reports={reports}
                  selectedReportId={selectedReport}
                  apiUrl={API_URL}
                />
              )}
            </>
          )}
        </div>

        {/* AI Chat Panel */}
        {chatOpen && (
          <ChatInterface 
            apiUrl={API_URL}
            onClose={() => setChatOpen(false)}
            onReportGenerated={(reportConfig) => {
              console.log('Report generated:', reportConfig);
              setCurrentView('builder');
            }}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Custom Report Builder • Build your own reports without vendor dependency</p>
      </footer>
    </div>
  );
}

export default App;
