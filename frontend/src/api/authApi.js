import axios from "axios";

const normalizeApiBaseUrl = (rawUrl) => {
  const fallback = "http://localhost:8000/api/v1";
  if (!rawUrl || typeof rawUrl !== "string") {
    return fallback;
  }
  const trimmed = rawUrl.trim().replace(/\/+$/, "");
  if (trimmed.endsWith("/api/v1")) {
    return trimmed;
  }
  return `${trimmed}/api/v1`;
};

const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
export const TOKEN_KEY = "lis_token";
export const USER_KEY = "lis_user";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail;
    let parsedDetail = null;

    if (Array.isArray(detail)) {
      parsedDetail = detail
        .map((item) => {
          if (typeof item === "string") {
            return item;
          }
          const loc = Array.isArray(item?.loc) ? item.loc.join(".") : "";
          const msg = item?.msg || "";
          return [loc, msg].filter(Boolean).join(": ");
        })
        .filter(Boolean)
        .join(" | ");
    } else if (detail && typeof detail === "object") {
      parsedDetail = detail?.msg || JSON.stringify(detail);
    } else if (typeof detail === "string") {
      parsedDetail = detail;
    }

    const message =
      parsedDetail ||
      error?.response?.data?.message ||
      error?.message ||
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(message));
  }
);

const decodeJwtPayload = (token) => {
  try {
    const payloadPart = token?.split(".")?.[1];
    if (!payloadPart) {
      return {};
    }
    const base64 = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const json = typeof atob === "function"
      ? atob(base64)
      : Buffer.from(base64, "base64").toString("utf-8");
    return JSON.parse(json);
  } catch {
    return {};
  }
};

const normalizeRole = (role) => (role === "admin" ? "admin" : "lawyer");

export const login = async ({ email, password, role }) => {
  const requestedRole = normalizeRole(role);

  const { data } = await apiClient.post("/auth/login", { email, password });
  const token = data?.access_token;
  if (!token) {
    throw new Error("Backend login did not return a token.");
  }

  const payload = decodeJwtPayload(token);
  const resolvedRole = payload?.role || requestedRole;

  return {
    token,
    user: {
      id: payload?.sub || email,
      role: resolvedRole,
      email,
      fullName: email,
    },
    expiresIn: 3600,
  };
};

export const signup = async (payload) => {
  const requestPayload = {
    full_name: payload?.fullName,
    email: payload?.email,
    password: payload?.password,
  };

  await apiClient.post("/auth/signup", requestPayload);

  // Auto-login after signup for smoother UX.
  return login({
    email: payload?.email,
    password: payload?.password,
    role: "lawyer",
  });
};

export const logout = async () => {
  try {
    await apiClient.post("/auth/logout");
  } catch {
    // Ignore backend logout failure and clear client state.
  }

  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const isMockApiEnabled = false;
