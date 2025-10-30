import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000"; // Your FastAPI backend base URL

export const startNavigator = async (repoUrl: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/navigator/start`, {
      repo_url: repoUrl,
    });
    return response.data;
  } catch (error: any) {
    console.error("Navigator error:", error);
    throw error.response?.data || error.message;
  }
};
