import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Home from "./pages/Home";
import SearchPage from "./pages/SearchPage";
import ResultPage from "./pages/ResultPage";
import Login from "./components/auth/Login";
import Signup from "./components/auth/Signup";
import LawyerDashboard from "./components/dashboard/LawyerDashboard";
import AdminDashboard from "./components/dashboard/AdminDashboard";
import { ProtectedRoute } from "./context/AuthContext";
import Navbar from "./components/common/Navbar";

const App = () => {
  const location = useLocation();
  const isDashboard = location.pathname.includes("dashboard");
  const isLogin = location.pathname.includes("login") || location.pathname.includes("signup");

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1e293b",
            color: "#f1f5f9",
            border: "1px solid #334155",
            borderRadius: "8px",
            boxShadow: "0 10px 40px rgba(0, 0, 0, 0.3)",
            padding: "16px",
            fontSize: "14px",
            fontWeight: "500",
          },
          success: {
            style: {
              borderLeft: "4px solid #10b981",
            },
          },
          error: {
            style: {
              borderLeft: "4px solid #ef4444",
            },
          },
        }}
      />

      {!isDashboard && !isLogin && <Navbar />}

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login-lawyer" element={<Login role="lawyer" />} />
        <Route path="/login-admin" element={<Login role="admin" />} />
        <Route path="/signup-lawyer" element={<Signup />} />

        <Route element={<ProtectedRoute allowedRoles={["lawyer"]} />}>
          <Route path="/lawyer/dashboard" element={<LawyerDashboard />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/results/:id" element={<ResultPage />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};

export default App;
