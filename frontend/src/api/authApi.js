import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
export const TOKEN_KEY = "lis_token";
export const USER_KEY = "lis_user";
const rawMockFlag = import.meta.env.VITE_USE_MOCK_API;
const USE_MOCK_API = rawMockFlag === undefined ? true : rawMockFlag !== "false";

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

export const shouldFallbackToMock = (error) => {
  // No HTTP response usually means backend is unreachable (network/CORS/server down).
  return !error?.response;
};

export const login = async ({ email, password, role }) => {
  if (USE_MOCK_API) {
    await sleep(650);

    if (!email || !password) {
      throw new Error("Email and password are required.");
    }

    const mockToken = `mock-jwt-token-${role || "lawyer"}-${Date.now()}`;
    return {
      token: mockToken,
      user: buildMockUser(role || "lawyer", email, role === "admin" ? "Admin Console" : "Arjun Mehra"),
      expiresIn: 3600,
    };
  }

  try {
    const { data } = await apiClient.post("/auth/login", { email, password, role });
    return data;
  } catch (error) {
    if (shouldFallbackToMock(error)) {
      const fallbackRole = role || "lawyer";
      return {
        token: `mock-jwt-token-${fallbackRole}-${Date.now()}`,
        user: buildMockUser(
          fallbackRole,
          email,
          fallbackRole === "admin" ? "Admin Console" : "Arjun Mehra"
        ),
        expiresIn: 3600,
      };
    }
    throw error;
  }
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

  try {
    const { data } = await apiClient.post("/auth/signup", payload);
    return data;
  } catch (error) {
    if (shouldFallbackToMock(error)) {
      return {
        token: `mock-jwt-token-lawyer-${Date.now()}`,
        user: buildMockUser("lawyer", payload?.email, payload?.fullName || "Demo User"),
        message: "Lawyer account created successfully.",
      };
    }
    throw error;
  }
};

export const logout = async () => {
  if (!USE_MOCK_API) {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Intentionally ignore backend logout failure and clear client state.
    }
  }

  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const isMockApiEnabled = USE_MOCK_API;
