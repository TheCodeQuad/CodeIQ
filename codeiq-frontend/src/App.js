import React, { useState } from "react";
import RepoInput from "./RepoInput";
import IRViewer from "./IRViewer";
import { generateIR } from "./api";

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async (repoUrl) => {
    setLoading(true);
    setResult(null);
    try {
      const res = await generateIR(repoUrl);
      setResult(res);
    } catch (err) {
      alert("❌ Error: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>🧠 CodeIQ — Intelligent Repo Analyzer</h1>
      <p className="subtitle">
        Automatically generate an <b>Intermediate Representation (IR)</b> for your GitHub repository.
      </p>

      <RepoInput onSubmit={handleGenerate} loading={loading} />
      <IRViewer result={result} />
    </div>
  );
}

export default App;
