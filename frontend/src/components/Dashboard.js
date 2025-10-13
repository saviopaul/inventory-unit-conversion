import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function Dashboard() {
  const [status, setStatus] = useState('idle');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [reports, setReports] = useState([]);
  const [schemas, setSchemas] = useState([]);
  const [screenshots, setScreenshots] = useState([]);

  useEffect(() => {
    loadSchemas();
    loadScreenshots();
  }, []);

  const loadSchemas = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/schemas`);
      setSchemas(response.data.schemas || []);
    } catch (error) {
      console.error('Error loading schemas:', error);
    }
  };

  const loadScreenshots = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/screenshots`);
      setScreenshots(response.data.screenshots || []);
    } catch (error) {
      console.error('Error loading screenshots:', error);
    }
  };

  const initializeScraper = async () => {
    setLoading(true);
    setMessage('Initializing scraper and logging in...');
    setStatus('loading');

    try {
      const response = await axios.post(`${API_URL}/api/scraper/initialize`);
      setMessage(response.data.message);
      setStatus('initialized');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const discoverReports = async () => {
    if (status !== 'initialized') {
      setMessage('Please initialize the scraper first');
      return;
    }

    setLoading(true);
    setMessage('Discovering all available reports...');

    try {
      const response = await axios.post(`${API_URL}/api/scraper/discover-reports`);
      setReports(response.data.reports || []);
      setMessage(`Found ${response.data.count} potential reports!`);
      setStatus('discovered');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const extractSchema = async (reportId) => {
    setLoading(true);
    setMessage(`Extracting schema for Report ${reportId}...`);

    try {
      const response = await axios.post(`${API_URL}/api/scraper/extract-schema`, {
        report_id: reportId
      });
      setMessage(`Schema extracted successfully! Found ${response.data.schema.columns.length} columns`);
      await loadSchemas();
      await loadScreenshots();
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const closeScraper = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/scraper/close`);
      setStatus('idle');
      setMessage('Scraper closed successfully');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Portal Scraper Status</h2>
        
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1">
            <div className="text-sm text-gray-500">Status</div>
            <div className="flex items-center mt-1">
              <span className={`badge ${
                status === 'idle' ? 'badge-gray' :
                status === 'loading' ? 'badge-blue' :
                status === 'initialized' || status === 'discovered' ? 'badge-green' :
                'bg-red-100 text-red-800'
              }`}>
                {status === 'idle' ? 'Not Started' :
                 status === 'loading' ? 'Processing...' :
                 status === 'initialized' ? 'Ready' :
                 status === 'discovered' ? 'Reports Discovered' :
                 status === 'error' ? 'Error' : status}
              </span>
            </div>
          </div>
          
          <div className="flex-1">
            <div className="text-sm text-gray-500">Schemas Extracted</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{schemas.length}</div>
          </div>
          
          <div className="flex-1">
            <div className="text-sm text-gray-500">Reports Found</div>
            <div className="text-2xl font-bold text-green-600 mt-1">{reports.length}</div>
          </div>
        </div>

        {message && (
          <div className={`p-4 rounded-lg mb-4 ${
            status === 'error' ? 'bg-red-50 text-red-700' :
            status === 'initialized' || status === 'discovered' ? 'bg-green-50 text-green-700' :
            'bg-blue-50 text-blue-700'
          }`}>
            {message}
          </div>
        )}

        <div className="flex space-x-3">
          <button
            onClick={initializeScraper}
            disabled={loading || status === 'initialized' || status === 'discovered'}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="btn-initialize"
          >
            {loading && status === 'loading' ? 'Initializing...' : '1. Initialize & Login'}
          </button>

          <button
            onClick={discoverReports}
            disabled={loading || status !== 'initialized'}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="btn-discover"
          >
            {loading && status !== 'loading' ? 'Discovering...' : '2. Discover Reports'}
          </button>

          <button
            onClick={() => extractSchema(474)}
            disabled={loading || status === 'idle'}
            className="btn-success disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="btn-extract-474"
          >
            3. Extract Report 474
          </button>

          <button
            onClick={closeScraper}
            disabled={loading || status === 'idle'}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="btn-close"
          >
            Close Scraper
          </button>
        </div>
      </div>

      {/* Discovered Reports */}
      {reports.length > 0 && (
        <div className="card">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Discovered Reports</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Report Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Link
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reports.map((report, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {report.text}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                      {report.href || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => window.open(`${API_URL}${report.href}`, '_blank')}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Screenshots */}
      {screenshots.length > 0 && (
        <div className="card">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Portal Screenshots</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {screenshots.map((screenshot, index) => (
              <div key={index} className="border rounded-lg p-2">
                <img
                  src={`${API_URL}/api/screenshots/${screenshot}`}
                  alt={screenshot}
                  className="w-full h-auto rounded cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => window.open(`${API_URL}/api/screenshots/${screenshot}`, '_blank')}
                />
                <p className="text-xs text-gray-600 mt-2 text-center">{screenshot}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
