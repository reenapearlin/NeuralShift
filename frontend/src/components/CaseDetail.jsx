import PDFViewer from "./PDFViewer";

function CaseDetail({ data, loading }) {
  return (
    <section className="panel content-panel">
      <div className="panel-title">Case Analysis</div>
      {loading && <p>Generating summary and report...</p>}
      {!loading && !data && <p>Select a case from results.</p>}

      {!loading && data && (
        <div className="case-detail">
          <div className="summary-card">
            <h3>Summary</h3>
            <p className="summary">{data.summary}</p>
          </div>

          <div className="report-card">
            <h3>Structured Report</h3>
            <div className="report-grid">
              {data.structured_report && Object.entries(data.structured_report).map(([k, v]) => (
                <div key={k} className="report-item">
                  <strong>{k.replaceAll("_", " ")}</strong>
                  <p>{v || "-"}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="keywords-card">
            <h4>Keywords</h4>
            <div className="badges">
              {(data.keywords || []).map((kw) => (
                <span key={kw} className="badge">{kw}</span>
              ))}
              {(data.keywords || []).length === 0 && <p>No keywords found</p>}
            </div>
          </div>

          <div className="pdf-card">
            <h4>PDF</h4>
            <PDFViewer pdfUrl={data.pdf_url} keywords={data.keywords} />
          </div>
        </div>
      )}
    </section>
  );
}

export default CaseDetail;
