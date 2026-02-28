import { useMemo, useState } from "react";
import { Download, ExternalLink, FileText } from "lucide-react";
import { apiClient } from "../../api/authApi";

const CaseFileViewer = ({ fileUrl, sourceUrl = null }) => {
  const [showPreview, setShowPreview] = useState(false);

  const previewProxyBase = useMemo(() => {
    const baseUrl = apiClient?.defaults?.baseURL || "";
    return `${baseUrl.replace(/\/api\/v1\/?$/, "")}/api/v1/precedents/preview`;
  }, []);

  const viewerUrl = useMemo(() => {
    if (!fileUrl) {
      return null;
    }
    if (/^https?:\/\//i.test(fileUrl)) {
      return `${previewProxyBase}?url=${encodeURIComponent(fileUrl)}`;
    }
    return fileUrl;
  }, [fileUrl, previewProxyBase]);

  const handleDownload = () => {
    if (!fileUrl) {
      return;
    }

    const ok = window.confirm("Do you want to download this case file PDF?");
    if (!ok) {
      return;
    }

    const link = document.createElement("a");
    link.href = fileUrl;
    const tail = fileUrl.split("/").pop()?.split("?")[0] || "";
    link.download = tail || "case-file.pdf";
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <section className="space-y-4 rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
      <h3 className="text-lg font-bold text-white">Case File & Documents</h3>

      {fileUrl ? (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => setShowPreview((prev) => !prev)}
              className="rounded-lg bg-amber-400 px-4 py-2 text-sm font-semibold text-slate-900"
            >
              {showPreview ? "Hide Preview" : "Preview Case File"}
            </button>
            <button
              type="button"
              onClick={handleDownload}
              className="flex items-center gap-2 rounded-lg border border-slate-500 px-4 py-2 text-sm font-semibold text-slate-200"
            >
              <Download className="h-4 w-4" />
              Download Case File
            </button>
            <a
              href={sourceUrl || fileUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 rounded-lg border border-slate-500 px-4 py-2 text-sm font-semibold text-slate-200"
            >
              <ExternalLink className="h-4 w-4" />
              Open Source
            </a>
          </div>

          {showPreview && viewerUrl && (
            <div className="overflow-hidden rounded-lg border border-slate-700/50">
              <iframe
                title="Case PDF Viewer"
                src={viewerUrl}
                className="h-96 w-full bg-white sm:h-[500px] lg:h-[600px]"
              />
            </div>
          )}
        </>
      ) : (
        <div className="rounded-lg border border-dashed border-slate-600 bg-slate-700/20 py-12 text-center">
          <FileText className="mx-auto mb-3 h-8 w-8 text-slate-500" />
          <p className="text-slate-400">Case file is unavailable</p>
        </div>
      )}
    </section>
  );
};

export default CaseFileViewer;
