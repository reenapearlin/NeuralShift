import { Link } from "react-router-dom";
import { ArrowRight, Zap } from "lucide-react";

const Home = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <div className="pointer-events-none absolute left-0 top-0 -z-10 h-96 w-96 rounded-full bg-amber-400/10 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-48 -z-10 h-96 w-96 rounded-full bg-blue-400/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 left-1/2 -z-10 h-96 w-96 -translate-x-1/2 rounded-full bg-cyan-400/10 blur-3xl" />

      <section className="relative px-4 py-12 sm:py-16 lg:py-24">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-amber-400/30 bg-amber-400/10 px-4 py-2">
            <Zap className="h-4 w-4 text-amber-400" />
            <span className="text-sm font-semibold text-amber-300">AI-Powered Legal Intelligence</span>
          </div>

          <h1 className="mb-6 text-4xl font-bold text-white sm:text-5xl lg:text-6xl">
            Nexorix
            <span className="block bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
              Legal Intelligence System
            </span>
          </h1>

          <p className="mb-8 text-lg text-slate-300 sm:text-xl">
            Intelligent retrieval system for cheque dishonour litigation. Powered by advanced AI to help lawyers and administrators manage Section 138 cases efficiently.
          </p>

          <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Link
              to="/login-lawyer"
              className="group flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-amber-400 to-amber-500 px-6 py-3 font-semibold text-slate-900 shadow-lg transition hover:shadow-xl hover:from-amber-300 hover:to-amber-400"
            >
              Lawyer
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
            </Link>
            <Link
              to="/login-admin"
              className="flex items-center justify-center gap-2 rounded-lg border border-slate-600 bg-slate-800/50 px-6 py-3 font-semibold text-white transition hover:border-blue-400/50 hover:bg-slate-700/50"
            >
              Admin
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-800 bg-slate-950/50 px-4 py-6 text-center text-sm text-slate-400">
        <p>&copy; 2024 Nexorix Legal Intelligence System. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Home;
