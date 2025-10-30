"use client";

import React, { useState } from "react";

export default function RepoForm() {
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!repoUrl.trim()) {
      setError("Please enter a valid repository URL.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/navigator/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || "Failed to analyze repository");

      setMessage("✅ Repository successfully cloned and processed!");
    } catch (err: any) {
      setError(`❌ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-2xl bg-white p-12 rounded-3xl shadow-2xl border-2 border-indigo-100 backdrop-blur-sm"
      >
        <div className="text-center mb-8">
          <h1 className="text-5xl font-black mb-3 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            CodeIQ Navigator
          </h1>
          <p className="text-gray-600 font-medium text-lg">
            Analyze any GitHub repository instantly
          </p>
        </div>

        <label className="block mb-6">
          <span className="text-base font-bold text-gray-800 mb-2 block">
            🔗 Git Repository URL
          </span>
          <input
            type="url"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/username/repository.git"
            className="mt-2 block w-full rounded-xl border-2 border-gray-300 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-200 p-4 text-gray-900 font-medium text-lg transition-all duration-200 placeholder:text-gray-400"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-4 mt-4 rounded-xl text-white font-bold text-lg shadow-lg transition-all duration-200 transform ${
            loading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 hover:scale-105 hover:shadow-xl"
          }`}
        >
          {loading ? "🔄 Analyzing..." : "✨ Analyze Repository"}
        </button>

        {message && (
          <div className="mt-6 p-4 bg-green-50 border-2 border-green-200 rounded-xl">
            <p className="text-green-700 text-center font-bold text-lg">
              {message}
            </p>
          </div>
        )}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border-2 border-red-200 rounded-xl">
            <p className="text-red-700 text-center font-bold text-lg">{error}</p>
          </div>
        )}
      </form>
    </div>
  );
}
