"use client";

import React, { useState } from "react";

export default function RepoForm() {
  const [repoUrl, setRepoUrl] = useState("");
  const [threshold, setThreshold] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [cfgLoading, setCfgLoading] = useState(false);
  const [cfgData, setCfgData] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAnalysisData(null);

    if (!repoUrl.trim()) {
      setError("Please enter a valid repository URL.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/navigator/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, threshold }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to analyze repository");

      setAnalysisData(data);
    } catch (err: any) {
      setError(`❌ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCFG = async (filePath: string) => {
    if (!analysisData || !analysisData.repo_name) return;
    setCfgLoading(true);
    setCfgData(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/navigator/generate_cfg", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_name: analysisData.repo_name,
          file_path: filePath,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate CFG");

      setCfgData(data);
      if (data.html_url) {
        window.open(`http://127.0.0.1:8000${data.html_url}`, "_blank");
      }
    } catch (err: any) {
      setError(`CFG Error: ${err.message}`);
    } finally {
      setCfgLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 text-slate-800">
      {/* Header */}
      <div className="bg-white shadow-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <h1 className="text-5xl font-extrabold text-center bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            CodeIQ Navigator
          </h1>
          <p className="text-slate-600 text-lg text-center mt-2 font-medium">
            Intelligent Code Analysis & Repository Explorer
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="bg-white p-8 rounded-2xl shadow-xl border border-slate-200 mb-10"
        >
          <div className="grid md:grid-cols-2 gap-6">
            <label className="block">
              <span className="text-base font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <span className="text-xl">🔗</span>
                Git Repository URL
              </span>
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repository.git"
                className="mt-2 block w-full rounded-xl border border-slate-300 bg-slate-50 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 p-4 text-slate-700 font-medium placeholder:text-slate-400 transition-all duration-200"
              />
            </label>

            <label className="block">
              <span className="text-base font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <span className="text-xl">🎯</span>
                Importance Threshold:{" "}
                <span className="text-indigo-600 font-bold">{threshold}</span>
              </span>
              <input
                type="range"
                min="1"
                max="10"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full h-3 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-500 mt-8"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>1 (More files)</span>
                <span>10 (Fewer files)</span>
              </div>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-4 mt-6 rounded-xl text-white font-bold text-lg shadow-md transition-all duration-300 ${
              loading
                ? "bg-slate-400 cursor-not-allowed"
                : "bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:via-purple-500 hover:to-pink-500 hover:shadow-xl"
            }`}
          >
            {loading ? "🔄 Analyzing Repository..." : "✨ Analyze Repository"}
          </button>
        </form>

        {/* Results */}
        {analysisData && (
          <div className="space-y-8">
            {/* Success */}
            <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-emerald-300 rounded-xl shadow-sm">
              <p className="text-emerald-700 text-center font-semibold flex items-center justify-center gap-2">
                ✅ {analysisData.message}
              </p>
            </div>

            {/* Statistics */}
            {analysisData.statistics && (
              <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-lg">
                <h2 className="text-3xl font-bold text-slate-800 mb-6 flex items-center gap-3">
                  📊 Analysis Statistics
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {[
                    {
                      label: "Files Analyzed",
                      value: analysisData.statistics.files_analyzed,
                      color: "text-indigo-600",
                    },
                    {
                      label: "Functions Found",
                      value: analysisData.statistics.total_functions,
                      color: "text-purple-600",
                    },
                    {
                      label: "Classes Found",
                      value: analysisData.statistics.total_classes,
                      color: "text-pink-600",
                    },
                    {
                      label: "Files Selected",
                      value: analysisData.filtering?.selected_count || 0,
                      color: "text-emerald-600",
                    },
                    {
                      label: "Files Excluded",
                      value: analysisData.filtering?.excluded_count || 0,
                      color: "text-amber-600",
                    },
                    {
                      label: "Dependencies",
                      value: analysisData.statistics.total_imports,
                      color: "text-blue-600",
                    },
                  ].map((stat, idx) => (
                    <div
                      key={idx}
                      className="bg-gradient-to-br from-white to-slate-50 p-6 rounded-xl border border-slate-200 text-center shadow-sm hover:shadow-md transition-all"
                    >
                      <p className={`text-4xl font-extrabold mb-1 ${stat.color}`}>
                        {stat.value}
                      </p>
                      <p className="text-slate-600 font-semibold text-sm">
                        {stat.label}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* File Lists */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Selected Files */}
              {analysisData.filtering?.selected_files?.length > 0 && (
                <div className="bg-white rounded-2xl p-6 border border-emerald-200 shadow-md">
                  <h2 className="text-2xl font-bold text-emerald-700 mb-4 flex items-center gap-2">
                    ✅ Selected Files ({analysisData.filtering.selected_files.length})
                  </h2>
                  <div className="max-h-96 overflow-y-auto space-y-2 pr-2">
                    {analysisData.filtering.selected_files.map((file: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-all border border-emerald-100"
                      >
                        <p className="text-sm font-mono text-slate-700 truncate flex-1 mr-2">
                          {file.path.split("\\").slice(-2).join("/")}
                        </p>
                        <div className="flex items-center gap-2">
                          <span className="px-3 py-1 bg-emerald-200 text-emerald-800 text-xs font-bold rounded-full">
                            {file.score}
                          </span>
                          <button
                            onClick={() => handleGenerateCFG(file.path)}
                            disabled={cfgLoading}
                            className="px-3 py-1 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold rounded-lg transition-all"
                          >
                            {cfgLoading ? "⏳" : "🔀 CFG"}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Excluded Files */}
              {analysisData.filtering?.excluded_files?.length > 0 && (
                <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-md">
                  <h2 className="text-2xl font-bold text-slate-700 mb-4 flex items-center gap-2">
                    🚫 Excluded Files (Top 20)
                  </h2>
                  <div className="max-h-96 overflow-y-auto space-y-2 pr-2">
                    {analysisData.filtering.excluded_files.map((file: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex justify-between items-center p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-all border border-slate-200"
                      >
                        <p className="text-sm font-mono text-slate-500 truncate flex-1">
                          {file.path.split("\\").slice(-2).join("/")}
                        </p>
                        <span className="ml-3 text-xs text-slate-600 px-2 py-1 bg-slate-100 rounded-full">
                          {file.score}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Repo Details */}
            <div className="bg-white rounded-2xl p-6 border border-indigo-200 shadow-md">
              <h2 className="text-2xl font-bold text-indigo-700 mb-4 flex items-center gap-2">
                📦 Repository Details
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                  <p className="text-slate-500 text-sm font-medium mb-1">Repository Name</p>
                  <p className="text-slate-800 font-bold">{analysisData.repo_name}</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                  <p className="text-slate-500 text-sm font-medium mb-1">Filter Threshold</p>
                  <p className="text-slate-800 font-bold">{analysisData.filtering?.threshold || threshold}</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                  <p className="text-slate-500 text-sm font-medium mb-1">Status</p>
                  <p className="text-emerald-600 font-bold flex items-center gap-1">✓ Complete</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-5 mt-8 bg-red-50 border border-red-200 rounded-xl shadow-sm">
            <p className="text-red-600 text-center font-semibold">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
