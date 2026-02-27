import { Link } from "react-router-dom";
import { Scale } from "lucide-react";

const Navbar = () => {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate-700/50 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-3 transition hover:opacity-80">
          <div className="rounded-lg bg-gradient-to-br from-amber-400 to-amber-500 p-2">
            <Scale className="h-6 w-6 text-slate-900" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Nexorix</h1>
            <p className="text-xs text-slate-400">Legal Intelligence System</p>
          </div>
        </Link>

      </div>
    </nav>
  );
};

export default Navbar;
