import { createContext, createElement, useCallback, useContext, useMemo, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

const TOKEN_KEY = "lis_token";
const USER_KEY = "lis_user";
const USERS_KEY = "lis_users";

const AuthContext = createContext(null);

const normalizeEmail = (email) => (email || "").trim().toLowerCase();

const getStoredUsers = () => {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
};

const setStoredUsers = (users) => {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
};

const getInitialAuth = () => {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);
    const user = storedUser ? JSON.parse(storedUser) : null;

    if (!token || !user) {
      return { token: null, user: null, role: null };
    }

    return { token, user, role: user.role || null };
  } catch {
    return { token: null, user: null, role: null };
  }
};

export const AuthProvider = ({ children }) => {
  const [authState, setAuthState] = useState(getInitialAuth);

  const persist = ({ token, user }) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    setAuthState({ token, user, role: user.role });
  };

  const login = useCallback(async (credentials, role) => {
    const normalizedRole = role === "admin" ? "admin" : "lawyer";
    const email = normalizeEmail(credentials?.email);
    const storedUsers = getStoredUsers();
    const matchedUser = email ? storedUsers[email] : null;

    const data = {
      token: `mock-token-${normalizedRole}-${Date.now()}`,
      user: {
        id: matchedUser?.id || `${normalizedRole}-${Date.now()}`,
        role: normalizedRole,
        email: email || "",
        fullName: matchedUser?.fullName || (normalizedRole === "admin" ? "Admin User" : "Lawyer User"),
      },
    };

    persist({ token: data.token, user: data.user });
    return data;
  }, []);

  const signup = useCallback(async (payload) => {
    const email = normalizeEmail(payload?.email);
    const fullName = (payload?.fullName || "").trim() || "Lawyer User";
    const userId = `lawyer-${Date.now()}`;

    if (email) {
      const storedUsers = getStoredUsers();
      storedUsers[email] = {
        id: storedUsers[email]?.id || userId,
        role: "lawyer",
        email,
        fullName,
      };
      setStoredUsers(storedUsers);
    }

    const data = {
      token: `mock-token-lawyer-${Date.now()}`,
      user: {
        id: userId,
        role: "lawyer",
        email,
        fullName,
      },
    };

    persist({ token: data.token, user: data.user });
    return data;
  }, []);

  const logout = useCallback(async () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setAuthState({ token: null, user: null, role: null });
  }, []);

  const value = useMemo(
    () => ({
      user: authState.user,
      role: authState.role,
      isAuthenticated: Boolean(authState.token && authState.user),
      login,
      signup,
      logout,
    }),
    [authState.user, authState.role, authState.token, login, signup, logout]
  );

  return createElement(AuthContext.Provider, { value }, children);
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
};

export const ProtectedRoute = ({ allowedRoles = [] }) => {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) {
    return createElement(Navigate, { to: "/", replace: true });
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(role)) {
    return createElement(Navigate, {
      to: role === "admin" ? "/admin/dashboard" : "/lawyer/dashboard",
      replace: true,
    });
  }

  return createElement(Outlet);
};
