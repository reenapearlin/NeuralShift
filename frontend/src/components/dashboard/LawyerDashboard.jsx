import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import {
  BriefcaseBusiness,
  FileSearch,
  FolderUp,
  Bookmark,
  LayoutDashboard,
  LogOut,
  Sparkles,
  Scale,
  Clock3,
  ArrowRight,
  Menu,
  X,
} from "lucide-react";
import { searchCases } from "../../api/searchApi";
import { useAuth } from "../../context/AuthContext";
import SearchForm from "../search/SearchForm";
import Filters from "../search/Filters";
import FileUpload from "../search/FileUpload";
import PrecedentChat from "../search/PrecedentChat";

const navItems = [
  { key: "dashboard", label: "Overview", icon: LayoutDashboard },
  { key: "search", label: "Search Cases", icon: FileSearch },
  { key: "upload", label: "Upload Case", icon: FolderUp },
  { key: "saved", label: "Saved Cases", icon: Bookmark },
];

const getBookmarksFromStorage = () => {
  try {
    const raw = localStorage.getItem("lis_bookmarks");
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const LawyerDashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [active, setActive] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [query, setQuery] = useState({
    chequeAmount: "",
    reasonForDishonour: "",
    noticeCompliance: "",
    limitationPeriod: "",
    courtLevel: "",
    freeText: "",
  });
  const [filters, setFilters] = useState({ fineAmount: "", jurisdiction: "", ranking: "" });
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [results, setResults] = useState([]);
  const [savedItems, setSavedItems] = useState([]);

  useEffect(() => {
    const refreshBookmarks = () => {
      setSavedItems(getBookmarksFromStorage());
    };

    refreshBookmarks();
    window.addEventListener("storage", refreshBookmarks);
    window.addEventListener("lis-bookmarks-updated", refreshBookmarks);

    return () => {
      window.removeEventListener("storage", refreshBookmarks);
      window.removeEventListener("lis-bookmarks-updated", refreshBookmarks);
    };
  }, []);

  const metrics = useMemo(
    () => [
      { label: "Matched Cases", value: results.length, hint: "From latest search", icon: Scale },
      { label: "Court", value: user?.courtOfPractice || "Not set", hint: "Primary practice", icon: BriefcaseBusiness },
      { label: "Experience", value: `${user?.experience || 0} years`, hint: "Professional profile", icon: Clock3 },
      { label: "Saved", value: savedItems.length, hint: "Bookmarked references", icon: Bookmark },
    ],
    [results.length, savedItems.length, user?.courtOfPractice, user?.experience]
  );

  const handleQueryChange = (event) => {
    const { name, value } = event.target;
    setQuery((prev) => ({ ...prev, [name]: value }));
  };

  const handleFilterChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const handleSearch = async (event) => {
    event.preventDefault();
    setLoadingSearch(true);

    try {
      const response = await searchCases(query, filters);
      setResults(response.items || []);
      toast.success(`${response.total || 0} matching cases found`);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoadingSearch(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    toast.success("Logged out successfully");
    navigate("/");
  };

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100">
      {/* Decorative background */}
      <div className="pointer-events-none absolute -left-20 top-0 h-80 w-80 rounded-full bg-amber-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 top-24 h-96 w-96 rounded-full bg-blue-400/10 blur-3xl" />

      <div className="relative flex min-h-screen">
        {/* Sidebar */}
        <aside
          className={`fixed left-0 top-0 z-40 h-screen w-72 border-r border-slate-800 bg-slate-950/95 backdrop-blur transition-transform duration-300 lg:sticky lg:translate-x-0 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          } p-5`}
        >
          {/* Header */}
          <div className="mb-8 rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-4">
            <div className="mb-3 flex items-center gap-2">
              <div className="rounded-lg bg-gradient-to-br from-amber-400 to-amber-500 p-2">
                <BriefcaseBusiness className="h-5 w-5 text-slate-900" />
              </div>
              <h2 className="text-sm font-bold tracking-wide text-slate-100">Lawyer Portal</h2>
            </div>
            <p className="text-sm font-semibold text-white">{user?.fullName || "Lawyer"}</p>
            <p className="text-xs text-slate-400">{user?.email || "profile@lawfirm.com"}</p>
          </div>

          {/* Navigation */}
          <nav className="mb-6 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = active === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => {
                    setActive(item.key);
                    setSidebarOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm font-medium transition ${
                    isActive
                      ? "bg-gradient-to-r from-amber-400 to-amber-500 text-slate-900 shadow-lg"
                      : "text-slate-300 hover:bg-slate-800/50 hover:text-white"
                  }`}
                >
                  <span className="flex items-center gap-2.5">
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </span>
                  {isActive && <ArrowRight className="h-4 w-4" />}
                </button>
              );
            })}
          </nav>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="mt-auto flex w-full items-center justify-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-sm font-semibold text-red-400 transition hover:bg-red-500/20 hover:border-red-500/50"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>

          {/* Close button for mobile */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="absolute right-4 top-4 rounded-lg p-1.5 hover:bg-slate-800 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {/* Mobile menu toggle */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="mb-4 rounded-lg p-2 hover:bg-slate-800 lg:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>

          {/* Page Header */}
          <header className="mb-8">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-3 py-1.5">
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-semibold uppercase tracking-wide text-emerald-300">Active</span>
                </div>
                <h1 className="mt-3 text-3xl font-bold text-white">Section 138 Intelligence</h1>
                <p className="mt-2 text-slate-400">
                  Search legal precedents, analyze cases, and build your legal strategy with AI assistance.
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setActive("search");
                  setSidebarOpen(false);
                }}
                className="hidden rounded-lg bg-gradient-to-r from-amber-400 to-amber-500 px-5 py-2.5 font-semibold text-slate-900 shadow-lg transition hover:shadow-xl sm:block"
              >
                New Search
              </button>
            </div>
          </header>

          {/* Metrics */}
          <section className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {metrics.map((item) => {
              const Icon = item.icon;
              return (
                <article
                  key={item.label}
                  className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition hover:border-amber-400/30"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-400">{item.label}</p>
                    <div className="rounded-lg bg-amber-400/10 p-2">
                      <Icon className="h-4 w-4 text-amber-400" />
                    </div>
                  </div>
                  <p className="mt-3 text-2xl font-bold text-white">{item.value}</p>
                  <p className="mt-1 text-xs text-slate-500">{item.hint}</p>
                </article>
              );
            })}
          </section>

          {/* Dashboard View */}
          {active === "dashboard" && (
            <section className="space-y-6">
              {/* Quick Actions */}
              <article className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
                <h3 className="mb-1 text-lg font-bold text-white">Quick Actions</h3>
                <p className="mb-4 text-slate-400">Jump to your most-used workflows</p>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={() => {
                      setActive("search");
                      setSidebarOpen(false);
                    }}
                    className="group rounded-lg border border-slate-600/50 bg-slate-700/20 p-4 text-left transition hover:border-amber-400/50 hover:bg-amber-400/5"
                  >
                    <FileSearch className="mb-2 h-5 w-5 text-amber-400" />
                    <p className="font-semibold text-white">Case Search</p>
                    <p className="mt-1 text-xs text-slate-400">Find relevant precedents and judgments</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setActive("upload");
                      setSidebarOpen(false);
                    }}
                    className="group rounded-lg border border-slate-600/50 bg-slate-700/20 p-4 text-left transition hover:border-blue-400/50 hover:bg-blue-400/5"
                  >
                    <FolderUp className="mb-2 h-5 w-5 text-blue-400" />
                    <p className="font-semibold text-white">Upload Case</p>
                    <p className="mt-1 text-xs text-slate-400">Submit files for AI-assisted analysis</p>
                  </button>
                </div>
              </article>

              {/* Recent Activity */}
              <article className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
                <h3 className="mb-4 text-lg font-bold text-white">Recent Activity</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-lg bg-slate-700/20 px-4 py-3 text-sm">
                    <span className="text-slate-300">Last login</span>
                    <span className="font-semibold text-white">Today</span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-slate-700/20 px-4 py-3 text-sm">
                    <span className="text-slate-300">Search results</span>
                    <span className="font-semibold text-white">{results.length} cases</span>
                  </div>
                </div>
              </article>
            </section>
          )}

          {/* Search View */}
          {active === "search" && (
            <section className="space-y-6">
              <SearchForm form={query} onChange={handleQueryChange} onSubmit={handleSearch} loading={loadingSearch} />
              <Filters filters={filters} onChange={handleFilterChange} />
              <PrecedentChat />

              {/* Results */}
              <article className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
                <h3 className="mb-1 text-lg font-bold text-white">Results</h3>
                <p className="mb-4 text-slate-400">{results.length} matching cases found</p>

                {results.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-slate-600 bg-slate-800/20 py-12 text-center">
                    <FileSearch className="mx-auto mb-3 h-8 w-8 text-slate-500" />
                    <p className="text-slate-400">Run a search to view matching cases</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {results.map((item) => (
                      <article
                        key={item.id}
                        className="overflow-hidden rounded-lg border border-slate-600/50 bg-slate-700/20 p-4 transition hover:border-amber-400/50 hover:bg-amber-400/5"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <h4 className="font-semibold text-white">{item.title}</h4>
                            <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-amber-300">
                              {item.source === "web" ? "Web Precedent (Live Scrape)" : "Local Approved Case"}
                            </p>
                            <p className="mt-2 text-sm text-slate-300">{item.summary}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => navigate(`/results/${item.id}`)}
                            className="whitespace-nowrap rounded-lg bg-amber-400 px-3 py-1.5 text-xs font-semibold text-slate-900 transition hover:bg-amber-300"
                          >
                            View
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </article>
            </section>
          )}

          {/* Upload View */}
          {active === "upload" && (
            <section className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
              <h3 className="mb-1 text-lg font-bold text-white">Upload Case Material</h3>
              <p className="mb-6 text-slate-400">Submit case files for AI-assisted extraction and analysis</p>
              <FileUpload metadata={{ uploaderRole: "lawyer", uploaderId: user?.id }} />
            </section>
          )}

          {/* Saved Cases View */}
          {active === "saved" && (
            <section className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
              <h3 className="mb-1 text-lg font-bold text-white">Saved Cases</h3>
              {(() => {
                const items = savedItems;
                if (!items.length) {
                  return <p className="mt-2 text-slate-400">No bookmarks yet.</p>;
                }
                return (
                  <div className="mt-4 space-y-3">
                    {items.map((item) => (
                      <article
                        key={item.id}
                        className="rounded-lg border border-slate-600/50 bg-slate-700/20 p-4"
                      >
                        <p className="font-semibold text-white">{item.title}</p>
                        <p className="mt-1 text-xs text-slate-400">
                          Saved: {item.savedAt ? new Date(item.savedAt).toLocaleString() : "N/A"}
                        </p>
                        <div className="mt-3 flex gap-2">
                          <button
                            type="button"
                            onClick={() => navigate(`/results/${item.id}`)}
                            className="rounded-lg bg-amber-400 px-3 py-1.5 text-xs font-semibold text-slate-900"
                          >
                            View
                          </button>
                          {item.sourceUrl && (
                            <a
                              href={item.sourceUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="rounded-lg border border-slate-500 px-3 py-1.5 text-xs font-semibold text-slate-200"
                            >
                              Source
                            </a>
                          )}
                        </div>
                      </article>
                    ))}
                  </div>
                );
              })()}
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default LawyerDashboard;
