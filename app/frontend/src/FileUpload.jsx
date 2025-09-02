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
      const res = await axios.get(
        `http://localhost:8000/analyze/${tableName}?analysis_type=${analyzeType}`
      );
      setAnalysis(prev => ({ ...prev, [index]: res.data }));
    } catch (err) {
      setAnalysis(prev => ({ 
        ...prev, 
        [index]: { error: err.response?.data?.detail || "Analysis failed" }
      }));
    }
    
    setAnalyzing(prev => ({ ...prev, [index]: false }));
  };

  const removeFile = (indexToRemove) => {
    setFiles(files.filter((_, index) => index !== indexToRemove));
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

        <div>
          <label>
            <input
              type="radio"
              name="analysisType"
              value="sql"
              checked={analyzeType === "sql"}
              onChange={() => setAnalyzeType("sql")}
            /> SQL
          </label>
          <label style={{ marginLeft: "16px" }}>
            <input
              type="radio"
              name="analysisType"
              value="ml"
              checked={analyzeType === "ml"}
              onChange={() => setAnalyzeType("ml")}
            /> ML
          </label>
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
                    ? 'Choose a file or drag it here (ML mode: single file only).'
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

                    <div className="result-section">
                      <h5>Sample Data</h5>
                      {renderTable(result.sample)}
                      <div className="rowCount">
                        <b>Total Rows:</b> {result.row_count}
                      </div>
                    </div>

                    <div className="actions">
                      <button
                        className="buttonSecondary"
                        onClick={() => handleAnalyze(result.table_name, index)}
                        disabled={analyzing[index]}
                      >
                        {analyzing[index] ? (
                          <>
                            <span className="spinner" /> Analyzing...
                          </>
                        ) : (
                          "Run Anomaly Check"
                        )}
                      </button>
                    </div>

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
                                      return (
                                        <>
                                          <p>{summary.slice(0, recIndex).trim()}</p>
                                          <div className="recommendations">
                                            <strong>Recommendations:</strong>
                                            <p>{summary.slice(recIndex + 'RECOMMENDATIONS:'.length).trim()}</p>
                                          </div>
                                        </>
                                      );
                                    }
                                    return <p>{summary}</p>;
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