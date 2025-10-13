import React, { useState, useEffect } from 'react';
import './ReportBuilder.css';

function ReportBuilder({ reports, selectedReportId, apiUrl }) {
  const [availableReports, setAvailableReports] = useState(reports);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [activeReportId, setActiveReportId] = useState(selectedReportId || null);
  const [reportColumns, setReportColumns] = useState({});
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (activeReportId && !reportColumns[activeReportId]) {
      fetchReportColumns(activeReportId);
    }
  }, [activeReportId]);

  const fetchReportColumns = async (reportId) => {
    try {
      const response = await fetch(`${apiUrl}/api/reports/${reportId}`);
      const data = await response.json();
      setReportColumns(prev => ({
        ...prev,
        [reportId]: data.columns
      }));
    } catch (error) {
      console.error('Error fetching columns:', error);
    }
  };

  const handleColumnSelect = (reportId, column, columnIndex) => {
    const newColumn = {
      report_id: reportId,
      column_name: column.column_name,
      qualified_name: column.qualified_name,
      display_name: column.display_name,
      column_index: columnIndex
    };

    // Check if already selected
    const exists = selectedColumns.find(
      c => c.report_id === reportId && c.column_index === columnIndex
    );

    if (exists) {
      // Remove
      setSelectedColumns(selectedColumns.filter(
        c => !(c.report_id === reportId && c.column_index === columnIndex)
      ));
    } else {
      // Add
      setSelectedColumns([...selectedColumns, newColumn]);
    }
  };

  const isColumnSelected = (reportId, columnIndex) => {
    return selectedColumns.some(
      c => c.report_id === reportId && c.column_index === columnIndex
    );
  };

  const handleGeneratePreview = async () => {
    if (selectedColumns.length === 0) {
      alert('Please select at least one column');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/reports/custom/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_columns: selectedColumns,
          filters: null,
          join_keys: null
        })
      });
      const data = await response.json();
      setPreviewData(data);
    } catch (error) {
      console.error('Error generating preview:', error);
      alert('Error generating preview');
    }
    setLoading(false);
  };

  const filteredColumns = activeReportId && reportColumns[activeReportId]
    ? reportColumns[activeReportId].filter(col =>
        col.column_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : [];

  return (
    <div className="report-builder">
      <div className="builder-header">
        <h2>🔨 Custom Report Builder</h2>
        <p>Select columns from any report to build your custom report</p>
      </div>

      <div className="builder-layout">
        {/* Left Panel - Column Selection */}
        <div className="column-selector">
          <div className="selector-header">
            <h3>Available Columns</h3>
            <select
              className="report-dropdown"
              value={activeReportId || ''}
              onChange={(e) => setActiveReportId(e.target.value)}
            >
              <option value="">Select a report...</option>
              {availableReports.map(report => (
                <option key={report.report_id} value={report.report_id}>
                  #{report.report_id} - {report.report_name.substring(0, 50)}
                </option>
              ))}
            </select>
          </div>

          {activeReportId && (
            <>
              <div className="search-box">
                <input
                  type="text"
                  placeholder="Search columns..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
              </div>

              <div className="columns-container">
                {filteredColumns.map((col, idx) => (
                  <div
                    key={idx}
                    className={`column-option ${
                      isColumnSelected(activeReportId, col.index) ? 'selected' : ''
                    }`}
                    onClick={() => handleColumnSelect(activeReportId, col, col.index)}
                  >
                    <div className="column-checkbox">
                      {isColumnSelected(activeReportId, col.index) && '✓'}
                    </div>
                    <div className="column-info">
                      <div className="column-name-text">{col.column_name}</div>
                      <div className="column-source">Report {activeReportId}</div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Right Panel - Selected Columns & Preview */}
        <div className="preview-panel">
          <div className="selected-columns-section">
            <h3>Selected Columns ({selectedColumns.length})</h3>
            {selectedColumns.length === 0 ? (
              <div className="empty-state">
                <p>No columns selected yet</p>
                <p className="empty-hint">Select columns from the left panel</p>
              </div>
            ) : (
              <div className="selected-list">
                {selectedColumns.map((col, idx) => (
                  <div key={idx} className="selected-item">
                    <span className="item-index">{idx + 1}</span>
                    <div className="item-info">
                      <span className="item-name">{col.column_name}</span>
                      <span className="item-source">Report {col.report_id}</span>
                    </div>
                    <button
                      className="remove-btn"
                      onClick={() => handleColumnSelect(col.report_id, col, col.column_index)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="action-buttons">
              <button
                className="btn-primary"
                onClick={handleGeneratePreview}
                disabled={selectedColumns.length === 0 || loading}
              >
                {loading ? 'Generating...' : '👁️ Generate Preview'}
              </button>
              <button
                className="btn-secondary"
                onClick={() => setSelectedColumns([])}
                disabled={selectedColumns.length === 0}
              >
                Clear All
              </button>
            </div>
          </div>

          {/* Preview Data */}
          {previewData && (
            <div className="preview-section">
              <h3>📊 Preview ({previewData.preview_rows} of {previewData.row_count} rows)</h3>
              <div className="preview-table-container">
                <table className="preview-table">
                  <thead>
                    <tr>
                      {previewData.columns.map((col, idx) => (
                        <th key={idx}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.data.slice(0, 10).map((row, rowIdx) => (
                      <tr key={rowIdx}>
                        {row.map((cell, cellIdx) => (
                          <td key={cellIdx}>{String(cell).substring(0, 50)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <button className="btn-export">💾 Export to CSV</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportBuilder;