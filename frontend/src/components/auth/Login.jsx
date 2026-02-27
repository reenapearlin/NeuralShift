import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { LockKeyhole, ShieldCheck, ArrowLeft } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const Login = ({ role = "lawyer" }) => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const roleText = role === "admin" ? "Admin" : "Lawyer";
  const Icon = role === "admin" ? ShieldCheck : LockKeyhole;
  const gradientClass = role === "admin" ? "from-blue-400 to-cyan-500" : "from-amber-400 to-orange-500";

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!form.email || !form.password) {
      toast.error("Email and password are required.");
      return;
    }
    if (form.password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);

    try {
      await login(form, role);
      toast.success(`${roleText} sign in successful`);
      navigate(role === "admin" ? "/admin/dashboard" : "/lawyer/dashboard");
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 px-4 py-10">
      <div className={`pointer-events-none absolute left-1/2 top-[-180px] h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-gradient-to-r ${gradientClass} opacity-10 blur-3xl`} />

      <Link
        to="/"
        className="absolute left-4 top-4 flex items-center gap-2 text-sm font-medium text-slate-400 transition hover:text-amber-400 sm:left-6 sm:top-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Link>

      <section className="relative mx-auto w-full max-w-md rounded-2xl border border-slate-700/50 bg-slate-900/85 p-8 shadow-2xl backdrop-blur">
        <div className="mb-8">
          <div className="mb-4 inline-flex items-center gap-3 rounded-lg border border-slate-600 bg-slate-800/50 px-3 py-2">
            <div className={`rounded-md bg-gradient-to-br ${gradientClass} p-1.5`}>
              <Icon className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-semibold uppercase tracking-wide text-slate-300">{roleText} Sign In</span>
          </div>

          <h1 className="text-3xl font-bold text-white">Welcome Back</h1>
          <p className="mt-2 text-slate-400">Enter any details to continue to your {roleText.toLowerCase()} dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-300">Email Address</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-600 bg-slate-800/60 px-4 py-2.5 text-white outline-none ring-offset-2 ring-offset-slate-900 transition placeholder:text-slate-500 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/30"
              placeholder="name@lawfirm.com"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-300">Password</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
              className="w-full rounded-lg border border-slate-600 bg-slate-800/60 px-4 py-2.5 text-white outline-none ring-offset-2 ring-offset-slate-900 transition placeholder:text-slate-500 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/30"
              placeholder="Enter password"
            />
          </div>

          <button
            disabled={loading}
            type="submit"
            className={`w-full rounded-lg bg-gradient-to-r ${gradientClass} px-4 py-3 font-semibold text-white shadow-lg transition disabled:cursor-not-allowed disabled:opacity-50 hover:shadow-xl active:scale-95`}
          >
            {loading ? "Signing in..." : `Sign In as ${roleText}`}
          </button>
        </form>

        {role !== "admin" && (
          <p className="mt-6 text-center text-xs text-slate-500">
            Need an account?{" "}
            <Link to="/signup-lawyer" className="font-semibold text-amber-400 hover:text-amber-300">
              Sign Up
            </Link>
          </p>
        )}
      </section>
    </div>
  );
};

export default Login;
