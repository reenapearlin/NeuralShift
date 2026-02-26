import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowLeft, Copy, Download, Share2 } from "lucide-react";
import CaseSummary from "../components/results/CaseSummary";
import StructuredReport from "../components/results/StructuredReport";
import CaseFileViewer from "../components/results/CaseFileViewer";
import { getCaseById } from "../api/searchApi";

const tabs = [
  { key: "summary", label: "Summary", icon: "📋" },
  { key: "report", label: "Structured Report", icon: "📊" },
  { key: "file", label: "Case File", icon: "📄" },
  { key: "highlights", label: "Key Points", icon: "⭐" },
];

const ResultPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("summary");

  useEffect(() => {
    const fetchCase = async () => {
      setLoading(true);
      try {
        const data = await getCaseById(id);
        setCaseData(data);
      } catch (error) {
        toast.error(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCase();
  }, [id]);

  const tabContent = useMemo(() => {
    if (!caseData) {
      return (
        <div className="rounded-lg border border-dashed border-slate-600 bg-slate-700/20 py-12 text-center">
          <p className="text-slate-400">Case data unavailable.</p>
        </div>
      );
    }

    if (activeTab === "summary") {
      return <CaseSummary title={caseData.title} summary={caseData.summary} />;
    }

    if (activeTab === "report") {
      return <StructuredReport report={caseData.structuredReport} />;
    }

    if (activeTab === "file") {
      return <CaseFileViewer fileUrl={caseData.caseFileUrl} keyPoints={caseData.keyPoints} />;
    }

    return (
      <section className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
        <h3 className="mb-4 text-lg font-bold text-white">Key Points & Highlights</h3>
        <ul className="space-y-2">
          {(caseData.keyPoints || []).map((point, idx) => (
            <li key={idx} className="flex gap-3 rounded-lg bg-slate-700/20 px-4 py-3 text-slate-300">
              <span className="flex-shrink-0 font-semibold text-amber-400">{idx + 1}.</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </section>
    );
  }, [activeTab, caseData]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="space-y-4 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-amber-300 border-t-transparent" />
          <p className="text-slate-400">Loading case details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Decorative background */}
      <div className="pointer-events-none absolute -left-20 top-0 h-80 w-80 rounded-full bg-amber-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 top-24 h-96 w-96 rounded-full bg-blue-400/10 blur-3xl" />

      <div className="relative mx-auto w-full max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <button
            onClick={() => navigate("/search")}
            className="flex w-fit items-center gap-2 text-sm font-medium text-slate-400 transition hover:text-amber-400"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Search
          </button>

          <div className="flex gap-2">
            <button
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                toast.success("Link copied to clipboard!");
              }}
              className="flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800/50 px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-700/50 hover:border-slate-500"
              title="Share this case"
            >
              <Share2 className="h-4 w-4" />
              Share
            </button>
            <button
              className="flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800/50 px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-700/50 hover:border-slate-500"
              title="Download case details"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          </div>
        </div>

        {/* Case Title Section */}
        {caseData && (
          <section className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
            <div className="mb-4 inline-flex items-center gap-2 rounded-lg border border-amber-400/30 bg-amber-400/10 px-3 py-1.5">
              <span className="text-xs font-semibold uppercase tracking-wide text-amber-300">Case Result</span>
            </div>
            <h1 className="text-2xl font-bold text-white md:text-3xl">{caseData.title}</h1>
            <p className="mt-3 text-slate-400">{caseData.description || "Legal case details and analysis"}</p>
          </section>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-1 overflow-x-auto rounded-lg border border-slate-700/50 bg-slate-900/30 p-1 sm:flex-wrap">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 whitespace-nowrap rounded-md px-4 py-2.5 text-sm font-medium transition ${
                activeTab === tab.key
                  ? "bg-gradient-to-r from-amber-400 to-amber-500 text-slate-900 shadow-lg"
                  : "text-slate-300 hover:bg-slate-800/50 hover:text-white"
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {tabContent}
      </div>
    </div>
  );
};

export default ResultPage;
