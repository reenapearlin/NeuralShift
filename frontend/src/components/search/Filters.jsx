const fieldClass =
  "w-full rounded-lg border border-slate-600/50 bg-slate-800/50 px-4 py-2.5 text-white outline-none ring-offset-2 ring-offset-slate-900 transition placeholder:text-slate-500 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/30";

const labelClass = "block text-sm font-semibold text-slate-300 mb-2";

const Filters = ({ filters, onChange }) => {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
      <h3 className="mb-6 text-lg font-bold text-white">Search Filters</h3>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div>
          <label className={labelClass}>Fine Amount (Min INR)</label>
          <input
            type="number"
            min="0"
            name="fineAmount"
            value={filters.fineAmount}
            onChange={onChange}
            className={fieldClass}
            placeholder="e.g., 50000"
          />
        </div>

        <div>
          <label className={labelClass}>Jurisdiction</label>
          <select name="jurisdiction" value={filters.jurisdiction} onChange={onChange} className={fieldClass}>
            <option value="">All Jurisdictions</option>
            <option value="Delhi">Delhi</option>
            <option value="Mumbai">Mumbai</option>
            <option value="Bengaluru">Bengaluru</option>
            <option value="Chennai">Chennai</option>
          </select>
        </div>

        <div>
          <label className={labelClass}>Case Ranking</label>
          <select name="ranking" value={filters.ranking} onChange={onChange} className={fieldClass}>
            <option value="">All Rankings</option>
            <option value="High">High Relevance</option>
            <option value="Medium">Medium Relevance</option>
            <option value="Low">Low Relevance</option>
          </select>
        </div>
      </div>
    </section>
  );
};

export default Filters;
