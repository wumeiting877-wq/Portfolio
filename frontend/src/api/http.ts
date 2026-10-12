import axios from "axios";
import { ElMessage } from "element-plus";
import { resolveApiError } from "../utils/apiError";

const http = axios.create({
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = String(error.config?.url || "");
    if (status === 401 && !url.includes("/api/auth/login")) {
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    const message = resolveApiError(error).message;
    if (status && status >= 400 && !url.includes("/api/auth/login")) {
      ElMessage.error(message);
    }
    return Promise.reject(error);
  },
);

export default http;
