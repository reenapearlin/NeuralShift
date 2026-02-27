const StructuredReport = ({ report }) => {
  const hasValue = (value) => {
    if (Array.isArray(value)) {
      return value.length > 0;
    }
    if (typeof value === "string") {
      return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
  };

  const SectionBlock = ({ title, items, type = "list" }) => (
    <div className="overflow-hidden rounded-lg border border-slate-700/50 bg-slate-800/30 p-5 backdrop-blur">
      <h4 className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-amber-300">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-400/10 text-xs">●</span>
        {title}
      </h4>
      {type === "list" ? (
        <ul className="space-y-2">
          {items.map((item, idx) => (
            <li
              key={idx}
              className="flex gap-3 rounded bg-slate-700/20 px-3 py-2 text-slate-300"
            >
              <span className="flex-shrink-0 font-semibold text-amber-400 text-sm">{idx + 1}.</span>
              <span className="text-sm">{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="rounded bg-slate-700/20 px-3 py-2 text-slate-300 text-sm leading-relaxed">{items}</p>
      )}
    </div>
  );

  return (
    <section className="space-y-4 rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
      <div className="mb-2">
        <h3 className="text-lg font-bold text-white">Structured Legal Report</h3>
        <p className="mt-1 text-sm text-slate-400">Detailed analysis of the case</p>
      </div>

      <div className="grid gap-4">
        {hasValue(report?.case_title) && <SectionBlock title="Case Title" items={report.case_title} type="text" />}
        {hasValue(report?.court) && <SectionBlock title="Court" items={report.court} type="text" />}
        {hasValue(report?.legal_issue) && (
          <SectionBlock title="Legal Issue" items={report.legal_issue} type="text" />
        )}
        {hasValue(report?.relevant_sections) && (
          <SectionBlock title="Relevant Sections" items={report.relevant_sections} type="list" />
        )}
        {hasValue(report?.limitation_analysis) && (
          <SectionBlock title="Limitation Analysis" items={report.limitation_analysis} type="text" />
        )}
        {hasValue(report?.penalty) && <SectionBlock title="Penalty" items={report.penalty} type="text" />}
        {hasValue(report?.judgement) && <SectionBlock title="Judgement" items={report.judgement} type="text" />}
        {hasValue(report?.key_principles) && (
          <SectionBlock title="Key Principles" items={report.key_principles} type="list" />
        )}
      </div>
    </section>
  );
};

export default StructuredReport;
