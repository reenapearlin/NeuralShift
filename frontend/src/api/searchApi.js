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
  {
    id: "case-138-002",
    title: "Nexa Metals vs Vardhan Exports",
    chequeAmount: 900000,
    fineAmount: 950000,
    jurisdiction: "Mumbai",
    ranking: "Medium",
    courtLevel: "High Court",
    reasonForDishonour: "Account Closed",
    noticeCompliance: "Compliant",
    limitationPeriod: "Within Limitation",
    summary:
      "Cheque return reason recorded as Account Closed. Court held closure equivalent to insufficiency for Section 138 proceedings.",
    keyPoints: ["Account closure treated as dishonour", "Demand notice valid", "Appeal dismissed"],
    structuredReport: {
      facts: ["Cheque amount: INR 9,00,000", "Account status: Closed before presentation"],
      legalIssues: ["Applicability of Section 138 where account is closed"],
      judgment: "Conviction maintained with modified sentence.",
      citations: ["(1998) 3 SCC 249"],
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

export const searchCases = async (query, filters) => {
  if (isMockApiEnabled) {
    await sleep(600);
    const result = applyFilters(mockCases, query, filters);

    return {
      total: result.length,
      items: result,
      // Example shape from backend:
      // { total: number, items: [{ id, title, summary, structuredReport, caseFileUrl, keyPoints }] }
    };
  }

  const { data } = await apiClient.post("/search/cases", { query, filters });
  return data;
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
  return data;
};
