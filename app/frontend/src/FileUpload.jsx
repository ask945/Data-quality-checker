import React, { useState } from "react";
import axios from "axios";

const FileUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState({});
  const [analyzing, setAnalyzing] = useState({});
  const [analyzeType, setAnalyzeType] = useState("sql");
  const [primaryIndex, setPrimaryIndex] = useState(0);
  const [relationships, setRelationships] = useState({}); // key: file index (non-primary) -> relation type
  const [serverRelationships, setServerRelationships] = useState(null);

  const [crossResults, setCrossResults] = useState(null);
  const [analyzingAll, setAnalyzingAll] = useState(false);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    // If ML mode is selected, only allow single file
    if (analyzeType === "ml" && selectedFiles.length > 1) {
      setFiles([selectedFiles[0]]); // Take only the first file
      setError("ML mode only supports single file upload. Only the first file was selected.");
    } else {
      setFiles(selectedFiles);
      setError("");
    }
    
    setResults([]);
    setAnalysis({});
    setPrimaryIndex(0);
    setRelationships({});
    setServerRelationships(null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.setAttribute('data-dragging', 'true');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.setAttribute('data-dragging', 'false');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.setAttribute('data-dragging', 'false');
    const droppedFiles = Array.from(e.dataTransfer.files);
    
    if (droppedFiles.length > 0) {
      // If ML mode is selected, only allow single file
      if (analyzeType === "ml" && droppedFiles.length > 1) {
        setFiles([droppedFiles[0]]); // Take only the first file
        setError("ML mode only supports single file upload. Only the first file was selected.");
      } else {
        setFiles(droppedFiles);
        setError("");
      }
      
      setResults([]);
      setAnalysis({});
      setPrimaryIndex(0);
      setRelationships({});
      setServerRelationships(null);
    }
  };

  const handleUploadAll = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    setError("");
    setResults([]);
    
    try {
      // Use single file endpoint for ML mode or when only one file
      if (analyzeType === "ml" || files.length === 1) {
        const formData = new FormData();
        formData.append("file", files[0]);
        
        const res = await axios.post(
          `http://localhost:8000/upload?analysis_type=${analyzeType}`, 
          formData, 
          {
            headers: { "Content-Type": "multipart/form-data" },
          }
        );
        
        setResults([{ ...res.data, filename: files[0].name }]);
      } else {
        // Use multiple file endpoint for SQL mode with multiple files
        const formData = new FormData();
        files.forEach((file) => {
          formData.append("files", file);
        });
        // Attach relationships metadata (by filename) if present
        try {
          const relationsPayload = {
            primaryIndex,
            primaryFilename: files[primaryIndex]?.name,
            relations: Object.fromEntries(
              Object.entries(relationships).map(([idx, rel]) => [files[Number(idx)]?.name, rel])
            ),
          };
          formData.append("relationships", JSON.stringify(relationsPayload));
        } catch (_) {}
        
        const res = await axios.post(
          `http://localhost:8000/upload-multiple?analysis_type=${analyzeType}`, 
          formData, 
          {
            headers: { "Content-Type": "multipart/form-data" },
          }
        );
        
        // Handle the response from the new endpoint
        if (res.data.results) {
          setResults(res.data.results);
          if (res.data.relationships) {
            setServerRelationships(res.data.relationships);
          } else {
            setServerRelationships(null);
          }
          // Reset cross-table results on new upload
          setCrossResults(null);
          
          // Show summary of upload results
          if (res.data.failed_uploads > 0) {
            setError(`${res.data.successful_uploads} files uploaded successfully, ${res.data.failed_uploads} failed`);
          }
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    }
    
    setUploading(false);
  };

  const handleAnalyze = async (tableName, index) => {
    setAnalyzing(prev => ({ ...prev, [index]: true }));
    try {
      const res = await axios.get(`http://localhost:8000/analyze/${tableName}?analysis_type=${analyzeType}`);
      setAnalysis(prev => ({ ...prev, [index]: res.data }));
    } catch (err) {
      setAnalysis(prev => ({ ...prev, [index]: { error: err.response?.data?.detail || "Analysis failed" } }));
    }
    setAnalyzing(prev => ({ ...prev, [index]: false }));
  };



  const handleAnalyzeAll = async () => {
    if (!results || results.length === 0) return;
    setAnalyzingAll(true);
    setError("");
    setCrossResults(null);
    setAnalysis({});
    try {
      // Run per-table analyses sequentially to keep UI state simple
      for (let i = 0; i < results.length; i++) {
        const tableName = results[i].table_name;
        try {
          const res = await axios.get(`http://localhost:8000/analyze/${tableName}?analysis_type=${analyzeType}`);
          setAnalysis(prev => ({ ...prev, [i]: res.data }));
        } catch (err) {
          setAnalysis(prev => ({ ...prev, [i]: { error: err.response?.data?.detail || "Analysis failed" } }));
        }
      }
      // Run cross-table analysis if relationships exist and more than one table
      if (serverRelationships && results.length > 1) {
        const payload = {
          relationships: serverRelationships,
          files: results.map(r => ({ filename: r.filename, table_name: r.table_name }))
        };
        try {
          const res = await axios.post(`http://localhost:8000/analyze-relationships`, payload);
          setCrossResults(res.data);
        } catch (err) {
          // Keep per-table results even if cross-table fails
          setError(err.response?.data?.detail || "Cross-table analysis failed");
        }
      }
    } finally {
      setAnalyzingAll(false);
    }
  };

  const removeFile = (indexToRemove) => {
    setFiles(files.filter((_, index) => index !== indexToRemove));
    // Adjust relationships and primary if necessary
    setRelationships((prev) => {
      const updated = {};
      Object.entries(prev).forEach(([idx, rel]) => {
        const numIdx = Number(idx);
        if (numIdx === indexToRemove) return;
        updated[numIdx > indexToRemove ? String(numIdx - 1) : String(numIdx)] = rel;
      });
      return updated;
    });
    setPrimaryIndex((prev) => {
      if (prev === indexToRemove) return 0;
      return prev > indexToRemove ? prev - 1 : prev;
    });
  };

  const clearAllFiles = () => {
    setFiles([]);
    setResults([]);
    setError("");
    setAnalysis({});
    const fileInput = document.getElementById('file-upload');
    if (fileInput) {
      fileInput.value = "";
    }
    setPrimaryIndex(0);
    setRelationships({});
    setServerRelationships(null);
  };

  function renderTable(data) {
    if (!data) return null;
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      const columns = Object.keys(data[0]);
      return (
        <div className="tableContainer">
          <table className="table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col}>{String(row[col])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
    if (typeof data === 'object' && !Array.isArray(data)) {
      return (
        <div className="tableContainer">
          <table className="table">
            <thead>
              <tr>
                <th>KEY</th>
                <th>VALUE</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data).map(([key, value]) => (
                <tr key={key}>
                  <td>{key}</td>
                  <td>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
    return <span>{String(data)}</span>;
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Data Quality Checker</h1>
        <p>Upload multiple CSV, Excel, or JSON files to run anomaly checks with a single click.</p>

        <div className="mode-selector">
          <h4>Analysis Mode</h4>
          <div className="radio-group">
            <label className={`radio-option ${analyzeType === "sql" ? "active" : ""}`}>
              <input
                type="radio"
                name="analysisType"
                value="sql"
                checked={analyzeType === "sql"}
                onChange={() => setAnalyzeType("sql")}
              />
              <span className="radio-custom"></span>
              <span className="radio-label">SQL Mode</span>
              <span className="radio-description">Comprehensive anomaly detection with relationship analysis</span>
            </label>
            <label className={`radio-option ${analyzeType === "ml" ? "active" : ""}`}>
              <input
                type="radio"
                name="analysisType"
                value="ml"
                checked={analyzeType === "ml"}
                onChange={() => setAnalyzeType("ml")}
              />
              <span className="radio-custom"></span>
              <span className="radio-label">ML Mode</span>
              <span className="radio-description">Machine learning-based pattern detection (single file)</span>
            </label>
          </div>
        </div>
      </div>

      <div className="card">
        {results.length === 0 ? (
          <>
            <label
              htmlFor="file-upload"
              className="dropzone"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                id="file-upload"
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                multiple={analyzeType !== "ml"} // Disable multiple for ML mode
                onChange={handleFileChange}
                disabled={uploading}
              />
              <p>
                {files.length > 0 
                  ? `Selected ${files.length} file${files.length > 1 ? 's' : ''}` 
                  : analyzeType === "ml" 
                    ? 'Choose a file or drag it here.'
                    : 'Choose files or drag them here.'
                }
              </p>
            </label>

            {files.length > 0 && !uploading && (
              <div className="files-list">
                <h4>Selected Files ({files.length})</h4>
                {files.map((file, index) => (
                  <div key={index} className="file-info">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                    <button 
                      onClick={() => removeFile(index)} 
                      className="clear-button" 
                      aria-label="Remove file"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  </div>
                ))}
                {analyzeType === "sql" && files.length > 1 && (
                  <div className="relationships">
                    <h4>Define Relationships</h4>
                    <div className="relationship-config">
                      <div className="primary-selector">
                        <label>Primary Dataset:</label>
                        <select 
                          value={primaryIndex} 
                          onChange={(e) => setPrimaryIndex(Number(e.target.value))}
                          className="select-styled"
                        >
                          {files.map((f, idx) => (
                            <option key={idx} value={idx}>{f.name}</option>
                          ))}
                        </select>
                      </div>
                      <div className="relationship-mappings">
                        {files.map((f, idx) => (
                          idx !== primaryIndex && (
                            <div key={idx} className="relationship-item">
                              <div className="relationship-label">
                                <span className="primary-file">{files[primaryIndex]?.name}</span>
                                <span className="relationship-arrow">↔</span>
                                <span className="related-file">{f.name}</span>
                              </div>
                              <select
                                value={relationships[idx] || "1:1"}
                                onChange={(e) => setRelationships((prev) => ({ ...prev, [idx]: e.target.value }))}
                                className="select-styled"
                              >
                                <option value="1:1">One-to-One (1:1)</option>
                                <option value="1:M">One-to-Many (1:M)</option>
                                <option value="M:1">Many-to-One (M:1)</option>
                                <option value="M:N">Many-to-Many (M:N)</option>
                              </select>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="actions">
              <button
                className="buttonPrimary"
                onClick={handleUploadAll}
                disabled={files.length === 0 || uploading}
              >
                {uploading ? (
                  <>
                    <span className="spinner" /> 
                    Uploading {files.length} file{files.length > 1 ? 's' : ''}...
                  </>
                ) : (
                  `Upload & Preview All (${files.length})`
                )}
              </button>
              {files.length > 0 && (
                <button className="buttonSecondary" onClick={clearAllFiles}>
                  Clear All
                </button>
              )}
            </div>
          </>
        ) : (
          <div className="resultsContainer">
            <div className="results-header">
              <h3>Upload Results ({results.length} files)</h3>
              <button className="buttonSecondary" onClick={clearAllFiles}>
                Upload New Files
              </button>
            </div>

            {/* 1) Previews of tables */}
            <div className="card nested-card">
              <h4>Previews</h4>
              {results.map((result, index) => (
                <div key={`preview-${index}`} className="result-section">
                  <div className="file-result-header">
                    <h5 style={{ marginBottom: 6 }}>{result.filename || result.table_name}</h5>
                    <span className="table-name">Table: {result.table_name}</span>
                  </div>
                  {result.status === 'error' ? (
                    <div className="alert alertError">{result.error}</div>
                  ) : (
                    <>
                      {renderTable(result.sample)}
                      <div className="rowCount"><b>Total Rows:</b> {result.row_count}</div>
                    </>
                  )}
                </div>
              ))}
            </div>

            {/* 2) Defined Relationships */}
            {Array.isArray(results) && results.length > 1 && serverRelationships && (
              <div className="card nested-card">
                <h4>Defined Relationships</h4>
                {(() => {
                  const rels = serverRelationships;
                  const primaryName = rels.primaryFilename || (results[rels.primaryIndex]?.filename || results[rels.primaryIndex]?.table_name);
                  const entries = rels.relations ? Object.entries(rels.relations) : [];
                  if (entries.length === 0) return <p>No relationships specified.</p>;
                  return (
                    <ul style={{ margin: 0, paddingLeft: 18 }}>
                      {entries.map(([fname, relType]) => (
                        <li key={fname}><b>{primaryName}</b> ↔ <b>{fname}</b>: {relType}</li>
                      ))}
                    </ul>
                  );
                })()}
              </div>
            )}

            {/* 3) Run Anomaly Check button */}
            <div className="actions" style={{ marginBottom: 16 }}>
              <button className="buttonSecondary" disabled={analyzingAll} onClick={handleAnalyzeAll}>
                {analyzingAll ? (<><span className="spinner" /> Running anomaly checks...</>) : ("Run Anomaly Check")}
              </button>
            </div>

            {/* 4) Outputs */}
            {crossResults && crossResults.total_anomalies > 0 && (
              <div className="card nested-card analysis-card">
                <h4>Cross-Table Anomalies</h4>
                <p><b>Primary:</b> {crossResults.primary}</p>
                <p><b>Total Issues:</b> {crossResults.total_anomalies}</p>
                <div className="tableContainer">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Related</th>
                        <th>Relation</th>
                        <th>Join Keys</th>
                        <th>Anomalies</th>
                      </tr>
                    </thead>
                    <tbody>
                      {crossResults.results.map((r, i) => (
                        <tr key={i}>
                          <td>{r.related}</td>
                          <td>{r.relation_type}</td>
                          <td>{Array.isArray(r.join_keys) ? r.join_keys.join(', ') : ''}</td>
                          <td>
                            {Array.isArray(r.anomalies) && r.anomalies.length > 0 ? (
                              <ul style={{ margin: 0, paddingLeft: 18 }}>
                                {r.anomalies.map((a, j) => (
                                  <li key={j}>{a.issue_type}: {a.details}</li>
                                ))}
                              </ul>
                            ) : (
                              <span>None</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {results.map((result, index) => (
              <div key={index} className="file-result card nested-card">
                {result.status === "error" ? (
                  <div className="error-result">
                    <div className="file-result-header">
                      <h4>{result.filename}</h4>
                      <span className="error-badge">Upload Failed</span>
                    </div>
                    <div className="alert alertError">{result.error}</div>
                  </div>
                ) : (
                  <>
                    <div className="file-result-header">
                      <h4>{result.filename || result.table_name}</h4>
                      <span className="table-name">Table: {result.table_name}</span>
                    </div>
                    {/* Preview moved to Previews section above */}
                    {/* Per-file run button removed in favor of unified Run Anomaly Check */}

                    {analyzing[index] && (
                      <div className="spinner-container">
                        <div className="spinner" />
                        <p>Analyzing data... this may take a moment.</p>
                      </div>
                    )}
                    
                    {analysis[index] && !analyzing[index] && (
                      <div className="card nested-card analysis-card">
                        {analysis[index].error ? (
                          <div className="alert alertError">{analysis[index].error}</div>
                        ) : (
                          <>
                            {analysis[index].formatted_output && (
                              <div className="analysis-section">
                                <h5>Anomaly Detection Summary</h5>
                                <div className="summary-content">
                                  {(() => {
                                    const summary = String(analysis[index].formatted_output);
                                    const recIndex = summary.indexOf('RECOMMENDATIONS:');
                                    if (recIndex !== -1) {
                                      const recommendations = summary.slice(recIndex + 'RECOMMENDATIONS:'.length).trim();
                                      const qualityScoreMatch = summary.match(/Data quality score:\s*(\d+(?:\.\d+)?)%/);
                                      const qualityScore = qualityScoreMatch ? parseFloat(qualityScoreMatch[1]) : null;
                                      
                                      return (
                                        <>
                                          <div style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                                            {(() => {
                                              const summaryText = summary.slice(0, recIndex).trim();
                                              const lines = summaryText.split('\n');
                                              const filteredLines = lines.filter((line, index) => {
                                                // Only show lines with detected anomalies (non-zero counts)
                                                if (line.includes('detected:')) {
                                                  const match = line.match(/detected:\s*(\d+)/);
                                                  if (match && parseInt(match[1]) === 0) {
                                                    return false;
                                                  }
                                                }
                                                // Also filter out LightGBM failure messages
                                                if (line.includes('✗ LightGBM anomaly detection failed:')) {
                                                  return false;
                                                }
                                                // Remove duplicate summary lines (keep only first occurrence)
                                                if (line.includes('Total anomalies found (events):') || 
                                                    line.includes('Unique rows flagged:')) {
                                                  const firstOccurrence = lines.findIndex(l => l === line);
                                                  if (firstOccurrence !== index) {
                                                    return false;
                                                  }
                                                }
                                                // Remove Anomaly breakdown line completely
                                                if (line.includes('Anomaly breakdown by method:')) {
                                                  return false;
                                                }
                                                return true;
                                              });
                                              
                                              // Convert technical logs to user-friendly text
                                              const userFriendlyLines = filteredLines.map(line => {
                                                if (line.includes('📋 ANOMALY DETECTION SUMMARY:')) {
                                                  return '📊 Analysis Summary:';
                                                }
                                                if (line.includes('Total anomalies found (events):')) {
                                                  return line.replace('Total anomalies found (events):', 'Total Issues Found:');
                                                }
                                                if (line.includes('Unique rows flagged:')) {
                                                  return line.replace('Unique rows flagged:', 'Affected Rows:');
                                                }
                                                if (line.includes('Data quality score:')) {
                                                  return line.replace('Data quality score:', 'Data Quality:');
                                                }
                                                if (line.includes('Methods used:')) {
                                                  return line.replace('Methods used:', 'Detection Methods:');
                                                }
                                                if (line.includes('detected:')) {
                                                  return line.replace('detected:', 'found:');
                                                }
                                                return line;
                                              });
                                              
                                              return userFriendlyLines.join('\n');
                                            })()}
                                          </div>
                                          {qualityScore !== 100 && (
                                            <div className="recommendations" style={{ marginTop: 12 }}>
                                              <strong>Recommendations:</strong>
                                              <p style={{ marginTop: 6 }}>{recommendations}</p>
                                            </div>
                                          )}
                                        </>
                                      );
                                    }
                                    return <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{summary}</pre>;
                                  })()}
                                </div>
                              </div>
                            )}
                            {Array.isArray(analysis[index].top_anomalies) && analysis[index].top_anomalies.length > 0 && (
                              <div className="analysis-section">
                                <h5>Top Anomalies Found</h5>
                                {renderTable(analysis[index].top_anomalies)}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        )}
        {error && <div className="alert alertError">{error}</div>}
      </div>
    </div>
  );
};

export default FileUpload;