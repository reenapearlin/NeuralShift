import { apiClient, isMockApiEnabled } from "./authApi";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const mockCases = [
  {
    id: "case-138-001",
    title: "R.K. Traders vs Mohan Industries",
    chequeAmount: 450000,
    fineAmount: 500000,
    jurisdiction: "Delhi",
    ranking: "High",
    courtLevel: "District Court",
    reasonForDishonour: "Insufficient Funds",
    noticeCompliance: "Compliant",
    limitationPeriod: "Within Limitation",
    summary:
      "The accused issued cheque no. 841237 dated 12-03-2024. The cheque was dishonoured for insufficient funds. Statutory notice was served within 30 days and complaint filed within limitation.",
    keyPoints: [
      "Cheque admitted by accused",
      "Legal notice served within statutory period",
      "No rebuttal evidence under Section 139 presumption",
    ],
    structuredReport: {
      facts: [
        "Cheque amount: INR 4,50,000",
        "Dishonour memo dated 15-03-2024",
        "Notice dated 20-03-2024",
      ],
      legalIssues: [
        "Whether ingredients of Section 138 NI Act are fulfilled",
        "Whether presumption under Section 139 stands unrebutted",
      ],
      judgment: "Conviction upheld. Compensation directed with simple imprisonment in default.",
      citations: ["(2010) 11 SCC 441", "(2001) 6 SCC 16"],
    },
    caseFileUrl: "https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf",
  },
];

const applyFilters = (cases, query = {}, filters = {}) => {
  return cases.filter((item) => {
    const amountOk = query.chequeAmount ? item.chequeAmount >= Number(query.chequeAmount) : true;
    const reasonOk = query.reasonForDishonour
      ? item.reasonForDishonour.toLowerCase().includes(query.reasonForDishonour.toLowerCase())
      : true;
    const noticeOk = query.noticeCompliance ? item.noticeCompliance === query.noticeCompliance : true;
    const limitationOk = query.limitationPeriod ? item.limitationPeriod === query.limitationPeriod : true;
    const courtOk = query.courtLevel ? item.courtLevel === query.courtLevel : true;

    const fineOk = filters.fineAmount ? item.fineAmount >= Number(filters.fineAmount) : true;
    const jurisdictionOk = filters.jurisdiction ? item.jurisdiction === filters.jurisdiction : true;
    const rankingOk = filters.ranking ? item.ranking === filters.ranking : true;

    return amountOk && reasonOk && noticeOk && limitationOk && courtOk && fineOk && jurisdictionOk && rankingOk;
  });
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

export const searchCases = async (query, filters) => {
  if (isMockApiEnabled) {
    await sleep(600);
    const result = applyFilters(mockCases, query, filters);

    return {
      total: result.length,
      items: result,
    };
  }

  const { data } = await apiClient.post("/search", toSearchPayload(query));
  const rows = data?.results ?? [];

  return {
    total: data?.count ?? data?.total ?? rows.length,
    items: rows.map((row) => ({
      id: row.case_id,
      title: row.case_title || `Case #${row.case_id}`,
      summary: row.short_snippet || "",
      tags: [row.court, row.year].filter(Boolean),
    })),
  };
};

export const getCaseById = async (id) => {
  if (isMockApiEnabled) {
    await sleep(450);
    const item = mockCases.find((entry) => entry.id === id);
    if (!item) {
      throw new Error("Case not found.");
    }
    return item;
  }

  const { data } = await apiClient.get(`/search/cases/${id}`);
  return {
    id,
    title: `Case #${id}`,
    summary: data?.summary || "",
    structuredReport: data?.structured_report || {},
    caseFileUrl: data?.pdf_path || null,
    keyPoints: [],
  };
};
