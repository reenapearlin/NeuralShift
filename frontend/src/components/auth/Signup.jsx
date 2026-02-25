import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../../context/AuthContext";

const defaultForm = {
  fullName: "",
  email: "",
  password: "",
};

const Signup = () => {
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);

    try {
      await signup(form);
      toast.success("Signup successful");
      navigate("/lawyer/dashboard");
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mx-auto w-full max-w-2xl rounded-2xl border border-slate-700/60 bg-slate-900/70 p-8 shadow-2xl backdrop-blur">
      <h1 className="mb-1 text-2xl font-bold text-white">Lawyer Sign Up</h1>
      <p className="mb-6 text-sm text-slate-300">No verification enabled right now. Enter any details and continue.</p>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <label className="mb-1 block text-sm text-slate-300">Full Name</label>
          <input
            name="fullName"
            value={form.fullName}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-white outline-none ring-amber-400 focus:ring"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-slate-300">Email</label>
          <input
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-white outline-none ring-amber-400 focus:ring"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-slate-300">Password</label>
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-white outline-none ring-amber-400 focus:ring"
          />
        </div>

        <div className="md:col-span-2 flex flex-wrap items-center gap-3 pt-1">
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-amber-400 px-6 py-2.5 font-semibold text-slate-900 transition hover:bg-amber-300 disabled:opacity-70"
          >
            {loading ? "Signing up..." : "Sign Up"}
          </button>
          <Link to="/login-lawyer" className="text-sm text-slate-200 hover:text-amber-300">
            Already have an account? Sign In
          </Link>
        </div>
      </form>
    </section>
  );
};

export default Signup;
