import { apiClient, isMockApiEnabled } from "./authApi";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const uploadCaseFile = async (file, onProgress, metadata = {}) => {
  if (!file) {
    throw new Error("Please select a file before uploading.");
  }

  if (isMockApiEnabled) {
    let progress = 0;
    while (progress < 100) {
      await sleep(120);
      progress += 20;
      if (onProgress) {
        onProgress(Math.min(progress, 100));
      }
    }

    return {
      message: "File uploaded successfully.",
      caseId: `uploaded-${Date.now()}`,
      filename: file.name,
      metadata,
    };
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
