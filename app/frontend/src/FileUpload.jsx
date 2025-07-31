import React, { useState } from "react";
import axios from "axios";
import { use } from "react";

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeType,setAnalyzeType]=useState("sql");

  

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError("");
    setAnalysis(null);
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
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setResult(null);
      setError("");
      setAnalysis(null);
    }
  };


  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);

    try {
      // ✅ Add the analysis_type as a query parameter
      const res = await axios.post(
        `http://localhost:8000/upload?analysis_type=${analyzeType}`, 
        formData, 
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    }
    setUploading(false);
  };

 const handleAnalyze = async () => {
    setAnalyzing(true);
    setAnalysis(null);
    try {
      // ✅ Add the analysis_type as a query parameter
      const res = await axios.get(
        `http://localhost:8000/analyze/${result.table_name}?analysis_type=${analyzeType}`
      );
      setAnalysis(res.data);
    } catch (err) {
      setAnalysis({ error: err.response?.data?.detail || "Analysis failed" });
    }
    setAnalyzing(false);
  };

  const clearFile = () => {
    setFile(null);
    setResult(null);
    setError("");
    setAnalysis(null);
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
        <p>Upload a CSV, Excel, or JSON file to run anomaly checks with a single click.</p>

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
        {!result ? (
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
                onChange={handleFileChange}
                disabled={uploading}
              />
              <p>{file ? `Selected: ${file.name}` : 'Choose a file or drag it here.'}</p>
            </label>

            {file && !uploading && (
               <div className="file-info">
                 <span className="file-name">{file.name}</span>
                 <button onClick={clearFile} className="clear-button" aria-label="Clear file">
                   <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                 </button>
               </div>
            )}

            <div className="actions">
              <button
                className="buttonPrimary"
                onClick={handleUpload}
                disabled={!file || uploading}
              >
                {uploading ? <><span className="spinner" /> Uploading...</> : "Upload & Preview"}
              </button>
            </div>
          </>
        ) : (
          <div className="resultsContainer">
            <h3>{result.table_name}</h3>
            <div className="result-section">
              <h4>Sample Data</h4>
              {renderTable(result.sample)}
              <div className="rowCount">
                <b>Total Rows:</b> {result.row_count}
              </div>
            </div>

            <div className="actions">
              <button
                className="buttonSecondary"
                onClick={handleAnalyze}
                disabled={analyzing}
              >
                {analyzing ? <><span className="spinner" /> Analyzing...</> : "Run Anomaly Check"}
              </button>
              <button className="buttonSecondary" onClick={clearFile}>Upload New File</button>
            </div>

            {analyzing && (
              <div className="spinner-container">
                <div className="spinner" />
                <p>Analyzing data... this may take a moment.</p>
              </div>
            )}
            
            {analysis && !analyzing && (
              <div className="card nested-card">
                {analysis.error ? (
                  <div className="alert alertError">{analysis.error}</div>
                ) : (
                  <>
                    {analysis.formatted_output && (
                      <div className="analysis-section">
                        <h4>Anomaly Detection Summary</h4>
                        <div className="summary-content">
                          {(() => {
                            const summary = String(analysis.formatted_output);
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
                    {Array.isArray(analysis.top_anomalies) && analysis.top_anomalies.length > 0 && (
                      <div className="analysis-section">
                        <h4>Top Anomalies Found</h4>
                        {renderTable(analysis.top_anomalies)}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        )}
        {error && <div className="alert alertError">{error}</div>}
      </div>
    </div>
  );
};

export default FileUpload;