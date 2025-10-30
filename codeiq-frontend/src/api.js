import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

export const generateIR = async (repoUrl) => {
  const response = await axios.post(`${API_BASE}/generate_ir`, null, {
    params: { repo_url: repoUrl },
  });
  return response.data;
};
