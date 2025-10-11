import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function ReportBuilder() {
  const [schemas, setSchemas] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [allColumns, setAllColumns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAllSchemas();
  }, []);

  const loadAllSchemas = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/schemas`);
      const schemasList = response.data.schemas || [];
      setSchemas(schemasList);

      // Load all columns from all schemas
      const columnsMap = new Map();
      
      for (const schema of schemasList) {
        const detailResponse = await axios.get(`${API_URL}/api/schemas/${schema.report_id}`);
        const schemaData = detailResponse.data.schema;
        
        schemaData.columns.forEach(column => {
          if (!columnsMap.has(column)) {
            columnsMap.set(column, {
              name: column,
              source: `Report ${schema.report_id}`,
              reportId: schema.report_id
            });
          }
        });
      }

      setAllColumns(Array.from(columnsMap.values()));
    } catch (error) {
      console.error('Error loading schemas:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleColumn = (column) => {
    setSelectedColumns(prev => {
      const exists = prev.find(c => c.name === column.name);
      if (exists) {
        return prev.filter(c => c.name !== column.name);
      } else {
        return [...prev, column];
      }
    });
  };

  const exportReport = () => {
    const reportData = {
      columns: selectedColumns.map(c => c.name),
      sources: selectedColumns.map(c => ({ column: c.name, source: c.source })),
      createdAt: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `custom_report_${Date.now()}.json`;
    a.click();
  };

  if (loading) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading report builder...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Custom Report Builder</h2>
        <p className="text-gray-600 mb-6">
          Select columns from all available reports to create your custom report. No vendor fees required!
        </p>

        {schemas.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No schemas available. Please extract schemas from the Dashboard first.</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Available Columns */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Available Columns ({allColumns.length})</h3>
              <div className="border rounded-lg p-4 h-96 overflow-y-auto bg-gray-50">
                {allColumns.map((column, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 hover:bg-white rounded cursor-pointer mb-2"
                    onClick={() => toggleColumn(column)}
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{column.name}</p>
                      <p className="text-xs text-gray-500">{column.source}</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={selectedColumns.some(c => c.name === column.name)}
                      onChange={() => {}}  
                      className="h-4 w-4 text-blue-600"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Columns */}
            <div>
              <h3 className="text-lg font-semibold mb-3">
                Selected Columns ({selectedColumns.length})
              </h3>
              <div className="border rounded-lg p-4 h-96 overflow-y-auto bg-blue-50">
                {selectedColumns.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No columns selected yet</p>
                ) : (
                  selectedColumns.map((column, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-white rounded mb-2"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{column.name}</p>
                        <p className="text-xs text-gray-500">{column.source}</p>
                      </div>
                      <button
                        onClick={() => toggleColumn(column)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {selectedColumns.length > 0 && (
          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={() => setSelectedColumns([])}
              className="btn-secondary"
            >
              Clear All
            </button>
            <button
              onClick={exportReport}
              className="btn-primary"
              data-testid="btn-export-report"
            >
              Export Report Configuration
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="card text-center">
          <p className="text-gray-600 text-sm">Total Reports</p>
          <p className="text-3xl font-bold text-blue-600">{schemas.length}</p>
        </div>
        <div className="card text-center">
          <p className="text-gray-600 text-sm">Available Columns</p>
          <p className="text-3xl font-bold text-green-600">{allColumns.length}</p>
        </div>
        <div className="card text-center">
          <p className="text-gray-600 text-sm">Selected Columns</p>
          <p className="text-3xl font-bold text-purple-600">{selectedColumns.length}</p>
        </div>
      </div>
    </div>
  );
}

export default ReportBuilder;
