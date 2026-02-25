import { useRef, useState } from "react";
import toast from "react-hot-toast";
import { UploadCloud, CheckCircle } from "lucide-react";
import { uploadCaseFile } from "../../api/uploadApi";

const FileUpload = ({ metadata = {}, onUploaded }) => {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const inputRef = useRef(null);

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) {
      return;
    }

    const allowed = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    if (!allowed.includes(selectedFile.type)) {
      toast.error("Only PDF or Word files are allowed.");
      return;
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      toast.error("File size must be less than 50MB.");
      return;
    }

    setFile(selectedFile);
    setProgress(0);
    setUploaded(false);
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please choose a file to upload.");
      return;
    }

    setLoading(true);
    try {
      const response = await uploadCaseFile(file, setProgress, metadata);
      toast.success("Case file uploaded successfully.");
      setUploaded(true);
      if (onUploaded) {
        onUploaded(response);
      }
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
      <h3 className="mb-2 text-lg font-bold text-white">Upload Case File</h3>
      <p className="mb-6 text-slate-400">Submit legal documents for AI-assisted analysis and extraction</p>

      <div
        onClick={() => !loading && inputRef.current?.click()}
        onDragOver={(event) => {
          if (!loading) {
            event.preventDefault();
            setDragActive(true);
          }
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(event) => {
          if (!loading) {
            event.preventDefault();
            setDragActive(false);
            handleFileSelect(event.dataTransfer.files?.[0]);
          }
        }}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition ${
          dragActive
            ? "border-amber-400 bg-amber-400/10"
            : "border-slate-600 bg-slate-700/20 hover:border-amber-300 hover:bg-amber-400/5"
        }`}
      >
        {uploaded ? (
          <>
            <CheckCircle className="mx-auto mb-3 h-10 w-10 text-green-400" />
            <p className="font-semibold text-green-400">File uploaded successfully</p>
            <p className="mt-1 text-sm text-slate-400">Your document is being processed</p>
          </>
        ) : (
          <>
            <UploadCloud className="mx-auto mb-3 h-10 w-10 text-amber-400" />
            <p className="text-sm font-medium text-white">Drag and drop your case file here</p>
            <p className="mt-1 text-xs text-slate-400">or click to browse • PDF, DOC, DOCX • Max 50MB</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".pdf,.doc,.docx"
          disabled={loading}
          onChange={(event) => handleFileSelect(event.target.files?.[0])}
        />
      </div>

      {file && (
        <div className="mt-6 space-y-4">
          <div className="rounded-lg bg-slate-700/30 px-4 py-3">
            <p className="text-xs text-slate-400 mb-1">Selected File</p>
            <p className="font-semibold text-white text-sm">{file.name}</p>
          </div>

          {loading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Upload progress</span>
                <span className="font-semibold text-amber-400">{progress}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-700/50 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-400 to-orange-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <button
          type="button"
          disabled={loading || !file}
          onClick={handleUpload}
          className="flex-1 rounded-lg bg-gradient-to-r from-amber-400 to-amber-500 px-4 py-2.5 font-semibold text-slate-900 shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-xl active:scale-95"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Uploading...
            </span>
          ) : (
            "Upload File"
          )}
        </button>
        {file && (
          <button
            type="button"
            onClick={() => {
              setFile(null);
              setProgress(0);
              setUploaded(false);
            }}
            className="rounded-lg border border-slate-600 bg-slate-800/50 px-4 py-2.5 font-semibold text-slate-300 transition hover:bg-slate-700/50 hover:border-slate-500"
          >
            Clear
          </button>
        )}
      </div>
    </section>
  );
};

export default FileUpload;
