import { useState } from "react";

const initialState = {
  section: "138",
  cheque_amount: 500000,
  notice_issued: true,
  limitation: "within limitation",
  dishonor_reason: "insufficient funds",
  nature_of_debt: "legally enforceable debt",
  court_filter: "",
  year_from: 2010,
  year_to: 2026,
};

function SearchForm({ onSearch, loading }) {
  const [form, setForm] = useState(initialState);

  const update = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const submit = (e) => {
    e.preventDefault();
    onSearch({
      ...form,
      cheque_amount: Number(form.cheque_amount),
      year_from: form.year_from ? Number(form.year_from) : null,
      year_to: form.year_to ? Number(form.year_to) : null,
    });
  };

  return (
    <form className="panel search-panel" onSubmit={submit}>
      <h3 className="panel-title">Search Cases</h3>
      <div className="grid">
        <label>
          Section
          <input value={form.section} onChange={(e) => update("section", e.target.value)} />
        </label>
        <label>
          Cheque Amount
          <input
            type="number"
            value={form.cheque_amount}
            onChange={(e) => update("cheque_amount", e.target.value)}
          />
        </label>
        <label>
          Notice Issued
          <select
            value={String(form.notice_issued)}
            onChange={(e) => update("notice_issued", e.target.value === "true")}
          >
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>
        <label>
          Dishonor Reason
          <input
            value={form.dishonor_reason}
            onChange={(e) => update("dishonor_reason", e.target.value)}
          />
        </label>
        <label>
          Nature of Debt
          <input
            value={form.nature_of_debt}
            onChange={(e) => update("nature_of_debt", e.target.value)}
          />
        </label>
        <label>
          Court Filter
          <input
            value={form.court_filter}
            onChange={(e) => update("court_filter", e.target.value)}
          />
        </label>
        <label>
          Year From
          <input
            type="number"
            value={form.year_from}
            onChange={(e) => update("year_from", e.target.value)}
          />
        </label>
        <label>
          Year To
          <input
            type="number"
            value={form.year_to}
            onChange={(e) => update("year_to", e.target.value)}
          />
        </label>
      </div>

      <div className="form-actions">
        <button className="btn primary" type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
        <button
          type="button"
          className="btn muted"
          onClick={() => setForm(initialState)}
          disabled={loading}
        >
          Reset
        </button>
      </div>
    </form>
  );
}

export default SearchForm;
