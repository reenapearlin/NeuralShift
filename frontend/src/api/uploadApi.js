import { apiClient } from "./authApi";

export const uploadCaseFile = async (file, onProgress, metadata = {}) => {
  if (!file) {
    throw new Error("Please select a file before uploading.");
  }

  const formData = new FormData();
  formData.append("file", file);
  Object.entries(metadata).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      formData.append(key, value);
    }
  });

  const { data } = await apiClient.post("/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) {
        return;
      }
      const percent = Math.round((event.loaded * 100) / event.total);
      onProgress(percent);
    },
  });

  return data;
};
