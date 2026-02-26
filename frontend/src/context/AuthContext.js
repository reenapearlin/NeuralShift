import { createContext, createElement, useCallback, useContext, useMemo, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import {
  login as loginApi,
  signup as signupApi,
  logout as logoutApi,
  TOKEN_KEY,
  USER_KEY,
} from "../api/authApi";

const AuthContext = createContext(null);

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
    const data = await loginApi({ ...credentials, role });
    if (!data?.token || !data?.user) {
      throw new Error("Login response was incomplete.");
    }
    persist({ token: data.token, user: data.user });
    return data;
  }, []);

  const signup = useCallback(async (payload) => {
    const data = await signupApi(payload);
    if (!data?.token || !data?.user) {
      throw new Error("Signup response was incomplete.");
    }
    persist({ token: data.token, user: data.user });
    return data;
  }, []);

  const logout = useCallback(async () => {
    await logoutApi();
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
