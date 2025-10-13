import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function SchemaViewer() {
  const [schemas, setSchemas] = useState([]);
  const [selectedSchema, setSelectedSchema] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSchemas();
  }, []);

  const loadSchemas = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/schemas`);
      setSchemas(response.data.schemas || []);
    } catch (error) {
      console.error('Error loading schemas:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewSchema = async (reportId) => {
    try {
      const response = await axios.get(`${API_URL}/api/schemas/${reportId}`);
      setSelectedSchema(response.data.schema);
    } catch (error) {
      console.error('Error loading schema details:', error);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading schemas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Extracted Schemas</h2>
        
        {schemas.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No schemas extracted yet. Go to Dashboard to extract schemas.</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {schemas.map((schema, index) => (
              <div
                key={index}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => viewSchema(schema.report_id)}
                data-testid={`schema-card-${schema.report_id}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg">Report {schema.report_id}</h3>
                  <span className="badge badge-blue">{schema.columns_count} columns</span>
                </div>
                <p className="text-xs text-gray-500 mb-2">
                  Extracted: {new Date(schema.extracted_at).toLocaleString()}
                </p>
                <button className="text-blue-600 text-sm hover:underline">
                  View Details →
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Schema Details Modal */}
      {selectedSchema && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-800">
              Report {selectedSchema.report_id} - Schema Details
            </h2>
            <button
              onClick={() => setSelectedSchema(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕ Close
            </button>
          </div>

          <div className="mb-4">
            <p className="text-sm text-gray-600">
              <strong>URL:</strong> {selectedSchema.report_url}
            </p>
            <p className="text-sm text-gray-600">
              <strong>Extracted:</strong> {new Date(selectedSchema.extracted_at).toLocaleString()}
            </p>
          </div>

          <h3 className="text-lg font-semibold mb-3">Columns ({selectedSchema.columns.length})</h3>
          
          {selectedSchema.columns.length === 0 ? (
            <p className="text-gray-500">No columns found in this report schema.</p>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-2">
              {selectedSchema.columns.map((column, index) => (
                <div
                  key={index}
                  className="bg-gray-50 border border-gray-200 rounded px-3 py-2 text-sm"
                >
                  {index + 1}. {column}
                </div>
              ))}
            </div>
          )}

          {selectedSchema.sample_data && selectedSchema.sample_data.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3">Sample Data</h3>
              <div className="bg-gray-50 border rounded p-4 overflow-x-auto">
                <pre className="text-xs">{JSON.stringify(selectedSchema.sample_data, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SchemaViewer;
