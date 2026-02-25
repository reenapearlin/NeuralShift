import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import {
  Shield,
  Users,
  FileClock,
  FileCheck,
  Database,
  LogOut,
  Menu,
  X,
  CheckCircle,
  XCircle,
  Send,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const AdminDashboard = () => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");

  const stats = useMemo(
    () => [
      { label: "Total Lawyers", value: 1248, icon: Users, color: "from-blue-400 to-blue-600" },
      { label: "Pending Cases", value: 86, icon: FileClock, color: "from-yellow-400 to-yellow-600" },
      { label: "Published Cases", value: 3912, icon: FileCheck, color: "from-green-400 to-green-600" },
      { label: "Total Records", value: 12560, icon: Database, color: "from-purple-400 to-purple-600" },
    ],
    []
  );

  const pendingUploads = [
    { id: "UP-4821", lawyer: "A. Singh", court: "Delhi High Court", status: "Pending", date: "2024-02-23" },
    { id: "UP-4822", lawyer: "R. Nair", court: "Bombay High Court", status: "Pending", date: "2024-02-22" },
    { id: "UP-4823", lawyer: "P. Kumar", court: "Chennai High Court", status: "Under Review", date: "2024-02-21" },
  ];

  const navItems = [
    { key: "dashboard", label: "Dashboard", icon: Shield },
    { key: "lawyers", label: "Manage Lawyers", icon: Users },
    { key: "cases", label: "Review Cases", icon: FileClock },
    { key: "publish", label: "Publish Cases", icon: Send },
    { key: "stats", label: "System Stats", icon: Database },
  ];

  const handleLogout = async () => {
    await logout();
    toast.success("Admin logged out");
    navigate("/");
  };

  const handleApprove = (id) => {
    toast.success(`Approved ${id}`);
  };

  const handleReject = (id) => {
    toast.error(`Rejected ${id}`);
  };

  const handlePublish = (id) => {
    toast.success(`Published ${id}`);
  };

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100">
      {/* Decorative background */}
      <div className="pointer-events-none absolute -left-20 top-0 h-80 w-80 rounded-full bg-blue-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 top-24 h-96 w-96 rounded-full bg-purple-400/10 blur-3xl" />

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
              <div className="rounded-lg bg-gradient-to-br from-blue-400 to-blue-600 p-2">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-sm font-bold tracking-wide text-slate-100">Admin Console</h2>
            </div>
            <p className="text-sm font-semibold text-white">{user?.fullName || "System Admin"}</p>
            <p className="text-xs text-slate-400">{user?.email || "admin@legalsystem.com"}</p>
          </div>

          {/* Navigation */}
          <nav className="mb-6 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => {
                    setActiveTab(item.key);
                    setSidebarOpen(false);
                  }}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition ${
                    isActive
                      ? "bg-gradient-to-r from-blue-400 to-blue-600 text-white shadow-lg"
                      : "text-slate-300 hover:bg-slate-800/50 hover:text-white"
                  }`}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span>{item.label}</span>
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
            <div>
              <h1 className="text-3xl font-bold text-white">System Dashboard</h1>
              <p className="mt-2 text-slate-400">Monitor lawyers, manage cases, and maintain system statistics</p>
            </div>
          </header>

          {/* Stats Grid */}
          <section className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((card) => {
              const Icon = card.icon;
              return (
                <article
                  key={card.label}
                  className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6 backdrop-blur transition hover:border-blue-400/30"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-400">{card.label}</p>
                      <p className="mt-2 text-3xl font-bold text-white">{card.value}</p>
                    </div>
                    <div className={`rounded-lg bg-gradient-to-br ${card.color} p-3 text-white`}>
                      <Icon className="h-6 w-6" />
                    </div>
                  </div>
                </article>
              );
            })}
          </section>

          {/* Tab Content */}
          {activeTab === "dashboard" && (
            <section className="space-y-6">
              {/* Quick Stats */}
              <article className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
                <h3 className="mb-4 text-lg font-bold text-white">System Health</h3>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div className="rounded-lg bg-slate-700/20 px-4 py-3">
                    <p className="text-sm text-slate-400">API Status</p>
                    <p className="mt-1 font-semibold text-green-400">Operational</p>
                  </div>
                  <div className="rounded-lg bg-slate-700/20 px-4 py-3">
                    <p className="text-sm text-slate-400">Database</p>
                    <p className="mt-1 font-semibold text-green-400">Connected</p>
                  </div>
                  <div className="rounded-lg bg-slate-700/20 px-4 py-3">
                    <p className="text-sm text-slate-400">Storage Usage</p>
                    <p className="mt-1 font-semibold text-yellow-400">72%</p>
                  </div>
                </div>
              </article>
            </section>
          )}

          {/* Cases Review Tab */}
          {activeTab === "cases" && (
            <section className="space-y-6">
              <article className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
                <h3 className="mb-1 text-lg font-bold text-white">Review Uploaded Cases</h3>
                <p className="mb-6 text-slate-400">Manage pending case submissions and approvals</p>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700/50 bg-slate-800/30">
                        <th className="px-4 py-3 text-left font-semibold text-slate-300">Upload ID</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-300">Lawyer</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-300">Court</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-300">Status</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-300">Date</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-300">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingUploads.map((item) => (
                        <tr
                          key={item.id}
                          className="border-b border-slate-700/30 transition hover:bg-slate-800/20"
                        >
                          <td className="px-4 py-3">
                            <code className="rounded bg-slate-800 px-2 py-1 text-xs font-mono text-amber-400">
                              {item.id}
                            </code>
                          </td>
                          <td className="px-4 py-3 text-white">{item.lawyer}</td>
                          <td className="px-4 py-3 text-slate-300">{item.court}</td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                                item.status === "Pending"
                                  ? "bg-yellow-400/10 text-yellow-400"
                                  : "bg-blue-400/10 text-blue-400"
                              }`}
                            >
                              <span className="h-1.5 w-1.5 rounded-full bg-current" />
                              {item.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400">{item.date}</td>
                          <td className="px-4 py-3">
                            <div className="flex gap-1.5">
                              <button
                                type="button"
                                onClick={() => handleApprove(item.id)}
                                className="rounded-lg bg-emerald-500/20 p-1.5 text-emerald-400 transition hover:bg-emerald-500/30"
                                title="Approve"
                              >
                                <CheckCircle className="h-4 w-4" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleReject(item.id)}
                                className="rounded-lg bg-red-500/20 p-1.5 text-red-400 transition hover:bg-red-500/30"
                                title="Reject"
                              >
                                <XCircle className="h-4 w-4" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handlePublish(item.id)}
                                className="rounded-lg bg-blue-500/20 p-1.5 text-blue-400 transition hover:bg-blue-500/30"
                                title="Publish"
                              >
                                <Send className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>
            </section>
          )}

          {/* Other Tabs */}
          {(activeTab === "lawyers" || activeTab === "publish" || activeTab === "stats") && (
            <section className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
              <h3 className="text-lg font-bold text-white">
                {activeTab === "lawyers" && "Manage Lawyers"}
                {activeTab === "publish" && "Publish Cases"}
                {activeTab === "stats" && "System Statistics"}
              </h3>
              <p className="mt-2 text-slate-400">This section is coming soon in the next update.</p>
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
