import { apiClient } from "./authApi";

export const fetchAdminStats = async () => {
  const { data } = await apiClient.get("/admin/stats");
  return data || {};
};

export const fetchPendingCases = async () => {
  const { data } = await apiClient.get("/admin/cases", {
    params: { status: "pending" },
  });
  return Array.isArray(data?.items) ? data.items : [];
};

export const fetchLawyers = async () => {
  const { data } = await apiClient.get("/admin/lawyers");
  return Array.isArray(data?.items) ? data.items : [];
};

export const approveCase = async (caseId) => {
  const { data } = await apiClient.put(`/admin/approve/${caseId}`);
  return data;
};

export const rejectCase = async (caseId) => {
  const { data } = await apiClient.put(`/admin/reject/${caseId}`);
  return data;
};
