import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
export const TOKEN_KEY = "lis_token";
export const USER_KEY = "lis_user";
const rawMockFlag = import.meta.env.VITE_USE_MOCK_API;
const USE_MOCK_API = rawMockFlag === "true";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
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
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(message));
  }
);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const buildMockUser = (role, email, fullName = "Demo User") => ({
  id: role === "admin" ? "admin-001" : "lawyer-001",
  role,
  email,
  fullName,
  barCouncilId: "BCI-2020-9842",
  courtOfPractice: "Delhi High Court",
  experience: "8",
});

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

  if (USE_MOCK_API) {
    await sleep(650);

    if (!email || !password) {
      throw new Error("Email and password are required.");
    }

    const mockToken = `mock-jwt-token-${requestedRole}-${Date.now()}`;
    return {
      token: mockToken,
      user: buildMockUser(
        requestedRole,
        email,
        requestedRole === "admin" ? "Admin Console" : "Arjun Mehra"
      ),
      expiresIn: 3600,
    };
  }

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
  if (USE_MOCK_API) {
    await sleep(700);

    if (!payload?.email || !payload?.password || !payload?.fullName) {
      throw new Error("Please fill all mandatory fields.");
    }

    return {
      token: `mock-jwt-token-lawyer-${Date.now()}`,
      user: buildMockUser("lawyer", payload.email, payload.fullName),
      message: "Lawyer account created successfully.",
    };
  }

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
  if (!USE_MOCK_API) {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Ignore backend logout failure and clear client state.
    }
  }

  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const isMockApiEnabled = USE_MOCK_API;
