import React from "react";
import ReactJson from 'react18-json-view';


const IRViewer = ({ result }) => {
  if (!result) return null;

  return (
    <div className="output">
      <h2>✅ IR Generated Successfully</h2>
      <p><strong>Files Processed:</strong> {result.files_processed}</p>

      <button
        className="download-btn"
        onClick={() => {
          const blob = new Blob([JSON.stringify(result.data, null, 2)], {
            type: "application/json",
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "ir_output.json";
          a.click();
        }}
      >
        ⬇️ Download IR JSON
      </button>

      <div className="json-container">
        <ReactJson src={result.data} collapsed={2} theme="rjv-default" />
      </div>
    </div>
  );
};

export default IRViewer;
