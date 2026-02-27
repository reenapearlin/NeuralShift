import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowLeft, FileText } from "lucide-react";
import SearchForm from "../components/search/SearchForm";
import Filters from "../components/search/Filters";
import FileUpload from "../components/search/FileUpload";
import PrecedentChat from "../components/search/PrecedentChat";
import { searchCases } from "../api/searchApi";

const SearchPage = () => {
  const navigate = useNavigate();

  const [query, setQuery] = useState({
    chequeAmount: "",
    reasonForDishonour: "",
    noticeCompliance: "",
    limitationPeriod: "",
    courtLevel: "",
    freeText: "",
  });
  const [filters, setFilters] = useState({ fineAmount: "", jurisdiction: "", ranking: "" });
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);

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
    setLoading(true);

    try {
      const data = await searchCases(query, filters);
      setResults(data.items || []);
      toast.success(`${data.total || 0} case(s) found`);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Decorative background */}
      <div className="pointer-events-none absolute -left-20 top-0 h-80 w-80 rounded-full bg-amber-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 top-24 h-96 w-96 rounded-full bg-blue-400/10 blur-3xl" />

      <div className="relative mx-auto w-full max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
        {/* Header */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <button
              onClick={() => navigate("/lawyer/dashboard")}
              className="mb-4 flex items-center gap-2 text-sm font-medium text-slate-400 transition hover:text-amber-400"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Case Search</h1>
            <p className="mt-2 text-slate-400">Find relevant precedents and legal references</p>
          </div>
        </div>

        {/* Search Section */}
        <SearchForm form={query} onChange={handleQueryChange} onSubmit={handleSearch} loading={loading} />

        {/* Filters */}
        <Filters filters={filters} onChange={handleFilterChange} />

        {/* Upload Section */}
        <FileUpload />

        {/* AI Chat Search */}
        <PrecedentChat />

        {/* Results Section */}
        <section className="rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
          <div className="mb-6">
            <h2 className="mb-1 text-lg font-bold text-white">Search Results</h2>
            <p className="text-slate-400">
              {results.length > 0 ? `${results.length} matching cases found` : "Run a search to view results"}
            </p>
          </div>

          {results.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-600 bg-slate-700/20 py-12 text-center">
              <FileText className="mx-auto mb-3 h-8 w-8 text-slate-500" />
              <p className="text-slate-400">No cases to display. Try adjusting your search criteria.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((item) => (
                <article
                  key={item.id}
                  className="overflow-hidden rounded-lg border border-slate-600/50 bg-slate-700/20 p-5 transition hover:border-amber-400/50 hover:bg-amber-400/5"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-white">{item.title}</h3>
                      <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-amber-300">
                        {item.source === "web" ? "Web Precedent (Live Scrape)" : "Local Approved Case"}
                      </p>
                      <p className="mt-2 text-sm text-slate-300 line-clamp-2">{item.summary}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {item.tags && item.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center rounded-full bg-slate-700/30 px-2.5 py-0.5 text-xs font-medium text-slate-300"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => navigate(`/results/${item.id}`)}
                      className="whitespace-nowrap rounded-lg bg-gradient-to-r from-amber-400 to-amber-500 px-4 py-2 text-sm font-semibold text-slate-900 shadow-lg transition hover:shadow-xl active:scale-95"
                    >
                      View Details
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default SearchPage;
