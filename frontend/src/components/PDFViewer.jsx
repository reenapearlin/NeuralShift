function PDFViewer({ pdfUrl, keywords }) {
  if (!pdfUrl) {
    return <p>No PDF URL available for this case.</p>;
  }

  const keywordText = Array.isArray(keywords)
    ? keywords.filter(Boolean).join(", ")
    : keywords || "";

  return (
    <div style={{ border: "1px solid #d1d5db", borderRadius: 8, overflow: "hidden" }}>
      {keywordText ? (
        <div
          style={{
            padding: "10px 12px",
            borderBottom: "1px solid #e5e7eb",
            background: "#f9fafb",
            fontSize: 14,
            color: "#374151",
          }}
        >
          Highlight keywords: {keywordText}
        </div>
      ) : null}

      <object data={pdfUrl} type="application/pdf" width="100%" height="560">
        <iframe title="case-pdf-viewer" src={pdfUrl} width="100%" height="560" style={{ border: 0 }} />
      </object>
    </div>
  );
}

export default PDFViewer;
