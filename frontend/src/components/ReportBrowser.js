import React, { useState, useEffect } from 'react';
import './ReportBrowser.css';

function ReportBrowser({ reports, onViewReport, apiUrl }) {
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportDetails, setReportDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchReportDetails = async (reportId) => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/reports/${reportId}`);
      const data = await response.json();
      setReportDetails(data);
    } catch (error) {
      console.error('Error fetching report details:', error);
    }
    setLoading(false);
  };

  const handleReportClick = (reportId) => {
    setSelectedReport(reportId);
    fetchReportDetails(reportId);
  };

  return (
    <div className="report-browser">
      <div className="browser-header">
        <h2>📊 Available Reports</h2>
        <p>Browse all {reports.length} GoFrugal reports and their schemas</p>
      </div>

      <div className="browser-content">
        {/* Report List */}
        <div className="report-list">
          {reports.map((report) => (
            <div
              key={report.report_id}
              className={`report-card ${selectedReport === report.report_id ? 'selected' : ''}`}
              onClick={() => handleReportClick(report.report_id)}
            >
              <div className="report-card-header">
                <span className="report-id">#{report.report_id}</span>
                <span className="report-badge">{report.column_count} columns</span>
              </div>
              <h3 className="report-title">{report.report_name}</h3>
              <div className="report-stats">
                <span>📄 {report.row_count.toLocaleString()} rows</span>
              </div>
              <button
                className="view-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewReport(report.report_id);
                }}
              >
                Build with this →
              </button>
            </div>
          ))}
        </div>

        {/* Report Details Panel */}
        <div className="report-details">
          {loading ? (
            <div className="loading-panel">
              <div className="spinner-small"></div>
              <p>Loading report details...</p>
            </div>
          ) : reportDetails ? (
            <>
              <div className="details-header">
                <h3>Report {reportDetails.report_id}</h3>
                <button
                  className="use-report-btn"
                  onClick={() => onViewReport(reportDetails.report_id)}
                >
                  🔨 Build Report
                </button>
              </div>

              <div className="details-section">
                <h4>{reportDetails.report_name}</h4>
                <p className="company-name">{reportDetails.company_name}</p>
                {reportDetails.filters && (
                  <p className="filters-info">{reportDetails.filters}</p>
                )}
              </div>

              <div className="details-section">
                <h4>📊 Statistics</h4>
                <div className="stats-grid">
                  <div className="stat-item">
                    <span className="stat-label">Columns</span>
                    <span className="stat-value">{reportDetails.column_count}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Rows</span>
                    <span className="stat-value">{reportDetails.row_count.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div className="details-section">
                <h4>📋 Columns ({reportDetails.columns.length})</h4>
                <div className="columns-list">
                  {reportDetails.columns.slice(0, 20).map((col, idx) => (
                    <div key={idx} className="column-item">
                      <span className="column-index">{idx + 1}</span>
                      <span className="column-name">{col.column_name}</span>
                    </div>
                  ))}
                  {reportDetails.columns.length > 20 && (
                    <p className="more-columns">
                      ... and {reportDetails.columns.length - 20} more columns
                    </p>
                  )}
                </div>
              </div>

              {reportDetails.sample_data && reportDetails.sample_data.length > 0 && (
                <div className="details-section">
                  <h4>👁️ Sample Data (First Row)</h4>
                  <div className="sample-data">
                    {reportDetails.columns.slice(0, 5).map((col, idx) => (
                      <div key={idx} className="sample-item">
                        <span className="sample-label">{col.column_name}:</span>
                        <span className="sample-value">
                          {reportDetails.sample_data[0] && reportDetails.sample_data[0][idx]
                            ? String(reportDetails.sample_data[0][idx]).substring(0, 30)
                            : 'N/A'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-selection">
              <div className="no-selection-icon">📊</div>
              <h3>Select a Report</h3>
              <p>Click on any report card to view its details and column schema</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportBrowser;
