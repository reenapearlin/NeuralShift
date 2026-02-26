const CaseSummary = ({ summary, title }) => {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
      <h3 className="mb-4 text-lg font-bold text-white">{title || "Case Summary"}</h3>
      <div className="prose prose-invert max-w-none">
        <p className="whitespace-pre-wrap leading-relaxed text-slate-300 text-base">
          {summary || "Summary not available."}
        </p>
      </div>
    </section>
  );
};

export default CaseSummary;
