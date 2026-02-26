function ResultsList({ results, loading, selectedCaseId, onSelectCase }) {
  return (
    <section className="panel results-panel">
      <div className="panel-title">Results</div>
      {loading && <p>Loading search results...</p>}
      {!loading && results.length === 0 && <p>No cases found.</p>}
      {!loading && results.length > 0 && (
        <ul className="results-list">
          {results.map((item) => (
            <li key={item.case_id} className="result-item">
              <button
                className={`result-card ${selectedCaseId === item.case_id ? "active" : ""}`}
                onClick={() => onSelectCase(item.case_id)}
              >
                <div className="meta">
                  <div className="title">{item.case_title}</div>
                  <div className="sub">{item.court} • {item.year}</div>
                </div>
                <div className="snippet">{item.short_snippet?.slice(0, 180)}{item.short_snippet?.length>180?"...":""}</div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default ResultsList;
