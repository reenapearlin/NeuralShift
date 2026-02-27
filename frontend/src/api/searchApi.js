import { apiClient } from "./authApi";

const toBackendOrigin = () => {
  const baseUrl = apiClient?.defaults?.baseURL || "";
  return baseUrl.replace(/\/api\/v1\/?$/, "");
};

const buildCaseFileUrl = (pdfPath) => {
  if (!pdfPath || typeof pdfPath !== "string") {
    return null;
  }
  if (/^https?:\/\//i.test(pdfPath)) {
    return pdfPath;
  }
  const cleaned = pdfPath.replace(/^\/+/, "");
  if (!cleaned) {
    return null;
  }
  return `${toBackendOrigin()}/storage/${cleaned}`;
};

const toSearchPayload = (query = {}) => ({
  cheque_amount: query.chequeAmount ? Number(query.chequeAmount) : undefined,
  dishonor_reason: query.reasonForDishonour || undefined,
  notice_period: undefined,
  nature_of_debt: undefined,
  court: query.courtLevel || undefined,
  year: undefined,
  bench: undefined,
  file_upload_flag: undefined,
});

const buildPrecedentQuery = (query = {}, filters = {}) => {
  const freeText = (query.freeText || "").trim();
  if (freeText) {
    return freeText;
  }
  const parts = [
    "Section 138 NI Act",
    query.chequeAmount ? `cheque amount ${query.chequeAmount}` : "",
    query.reasonForDishonour ? `dishonour reason ${query.reasonForDishonour}` : "",
    query.noticeCompliance ? `notice compliance ${query.noticeCompliance}` : "",
    query.limitationPeriod ? `limitation ${query.limitationPeriod}` : "",
    query.courtLevel ? `court level ${query.courtLevel}` : "",
    filters.jurisdiction ? `jurisdiction ${filters.jurisdiction}` : "",
  ].filter(Boolean);
  return parts.join(" ").trim();
};

export const searchCases = async (query, filters = {}) => {
  const localRequest = apiClient.post("/search", toSearchPayload(query));
  const precedentQuery = buildPrecedentQuery(query, filters);
  const precedentRequest = precedentQuery.length >= 2
    ? apiClient.get("/precedents/search", { params: { q: precedentQuery, top_n: 5 } })
    : Promise.resolve({ data: { results: [] } });

  const [localResult, precedentResult] = await Promise.allSettled([localRequest, precedentRequest]);

  const localRows = localResult.status === "fulfilled"
    ? (localResult.value?.data?.results ?? [])
    : [];
  const localItems = localRows.map((row) => ({
    id: row.case_id,
    title: row.case_title || `Case #${row.case_id}`,
    summary: row.short_snippet || "",
    tags: [row.court, row.year].filter(Boolean),
    source: "local",
  }));

  let precedentRows = precedentResult.status === "fulfilled"
    ? (precedentResult.value?.data?.results ?? [])
    : [];
  if (precedentRows.length === 0) {
    try {
      const fallback = await apiClient.get("/precedents/search", {
        params: { q: "section 138 cheque bounce", top_n: 5 },
      });
      precedentRows = fallback?.data?.results ?? [];
    } catch {
      // Keep local-only results if fallback scrape also fails.
    }
  }
  const precedentItems = precedentRows.map((row, index) => ({
    id: `web:${encodeURIComponent(row.url || "")}`,
    title: row.title || "Web Precedent",
    summary: row.snippet || "",
    tags: [
      `Score: ${row.score ?? 0}`,
      ...(Array.isArray(row.keywords) ? row.keywords.slice(0, 3) : []),
    ],
    source: "web",
    url: row.url,
    score: row.score,
    keywords: Array.isArray(row.keywords) ? row.keywords : [],
  }));

  const items = [...localItems, ...precedentItems];
  return {
    total: items.length,
    items,
  };
};

export const chatPrecedents = async (message, topN = 5) => {
  const cleaned = (message || "").trim();
  if (!cleaned) {
    return { query: "", results: [] };
  }
  const { data } = await apiClient.get("/precedents/search", {
    params: { q: cleaned, top_n: topN },
  });
  return {
    query: data?.query || cleaned,
    results: Array.isArray(data?.results) ? data.results : [],
  };
};

export const getCaseById = async (id) => {
  if (typeof id === "string" && id.startsWith("web:")) {
    const encodedUrl = id.slice(4);
    const url = decodeURIComponent(encodedUrl);
    try {
      const { data } = await apiClient.get("/precedents/view", {
        params: { url },
      });
      const structuredReport = data?.structured_report || {};
      return {
        id,
        title: data?.case_title || structuredReport?.case_title || "Not Specified",
        summary: data?.summary || "",
        structuredReport,
        caseFileUrl: data?.pdf_path || url || null,
        keyPoints: Array.isArray(data?.highlighted_keywords) && data.highlighted_keywords.length > 0
          ? data.highlighted_keywords
          : Array.isArray(data?.key_points)
          ? data.key_points
          : Array.isArray(structuredReport?.key_principles)
          ? structuredReport.key_principles
          : [],
        sourceUrl: data?.source_url || url || null,
        isWebPrecedent: true,
      };
    } catch {
      return {
        id,
        title: "Web Precedent",
        summary: "Summary currently unavailable. Open source and retry.",
        structuredReport: {
          case_title: "Web Precedent",
          court: "Not Specified",
          legal_issue: "Not Specified",
          relevant_sections: ["Not Specified"],
          limitation_analysis: "Not Specified",
          penalty: "Not Specified",
          judgement: "Not Specified",
          key_principles: ["Not Specified"],
        },
        caseFileUrl: url || null,
        keyPoints: ["Not Specified"],
        sourceUrl: url || null,
        isWebPrecedent: true,
      };
    }
  }

  const { data } = await apiClient.get(`/search/cases/${id}`);
  const structuredReport = data?.structured_report || {};

  return {
    id,
    title: data?.case_title || structuredReport?.case_title || `Case #${id}`,
    summary: data?.summary || "",
    structuredReport,
    caseFileUrl: buildCaseFileUrl(data?.pdf_path),
    keyPoints: Array.isArray(data?.key_points)
      ? data.key_points
      : Array.isArray(structuredReport?.key_principles)
      ? structuredReport.key_principles
      : [],
    sourceUrl: null,
    isWebPrecedent: false,
  };
};
