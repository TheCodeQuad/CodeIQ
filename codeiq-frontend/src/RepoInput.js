import React, { useState } from "react";

const RepoInput = ({ onSubmit, loading }) => {
  const [repoUrl, setRepoUrl] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (repoUrl.trim() === "") return alert("Enter a GitHub URL!");
    onSubmit(repoUrl);
  };

  return (
    <form onSubmit={handleSubmit} className="repo-form">
      <input
        type="text"
        placeholder="🔗 Enter GitHub Repository URL"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
      />
      <button type="submit" disabled={loading}>
        {loading ? "Processing..." : "Generate IR"}
      </button>
    </form>
  );
};

export default RepoInput;
