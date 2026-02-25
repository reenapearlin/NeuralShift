import { Search } from "lucide-react";

const fieldClass =
  "w-full rounded-lg border border-slate-600/50 bg-slate-800/50 px-4 py-2.5 text-white outline-none ring-offset-2 ring-offset-slate-900 transition placeholder:text-slate-500 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/30";

const labelClass = "block text-sm font-semibold text-slate-300 mb-2";

const SearchForm = ({ form, onChange, onSubmit, loading }) => {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
      <div className="mb-6">
        <h2 className="mb-2 text-lg font-bold text-white">Section 138 Advanced Search</h2>
        <p className="text-slate-400">Find relevant precedents using detailed case parameters</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        {/* First Row */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <label className={labelClass}>Cheque Amount (INR)</label>
            <input
              type="number"
              min="0"
              name="chequeAmount"
              value={form.chequeAmount}
              onChange={onChange}
              className={fieldClass}
              placeholder="e.g., 100000"
            />
          </div>

          <div>
            <label className={labelClass}>Reason for Dishonour</label>
            <select name="reasonForDishonour" value={form.reasonForDishonour} onChange={onChange} className={fieldClass}>
              <option value="">All Reasons</option>
              <option value="Insufficient Funds">Insufficient Funds</option>
              <option value="Account Closed">Account Closed</option>
              <option value="Signature Mismatch">Signature Mismatch</option>
              <option value="Payment Stopped">Payment Stopped</option>
            </select>
          </div>

          <div>
            <label className={labelClass}>Notice Compliance</label>
            <select name="noticeCompliance" value={form.noticeCompliance} onChange={onChange} className={fieldClass}>
              <option value="">Any Status</option>
              <option value="Compliant">Compliant</option>
              <option value="Non-Compliant">Non-Compliant</option>
            </select>
          </div>
        </div>

        {/* Second Row */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-2">
          <div>
            <label className={labelClass}>Limitation Period</label>
            <select name="limitationPeriod" value={form.limitationPeriod} onChange={onChange} className={fieldClass}>
              <option value="">Any Period</option>
              <option value="Within Limitation">Within Limitation</option>
              <option value="Time Barred">Time Barred</option>
            </select>
          </div>

          <div>
            <label className={labelClass}>Court Level</label>
            <select name="courtLevel" value={form.courtLevel} onChange={onChange} className={fieldClass}>
              <option value="">All Courts</option>
              <option value="District Court">District Court</option>
              <option value="Sessions Court">Sessions Court</option>
              <option value="High Court">High Court</option>
              <option value="Supreme Court">Supreme Court</option>
            </select>
          </div>
        </div>

        {/* Search Button */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-amber-400 to-amber-500 px-6 py-3 font-semibold text-slate-900 shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-xl active:scale-95"
          >
            <Search className="h-5 w-5" />
            {loading ? "Searching..." : "Search Cases"}
          </button>
        </div>
      </form>
    </section>
  );
};

export default SearchForm;
