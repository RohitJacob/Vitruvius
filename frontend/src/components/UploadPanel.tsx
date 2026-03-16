import { useCallback, useRef, useState } from "react";
import { useReportStore } from "../stores/reportStore";
import { uploadFiles } from "../api/client";
import ThemeToggle from "./ThemeToggle";

export default function UploadPanel() {
  const { photoFiles, setPhotoFiles, templateFile, setTemplateFile, setSessionId, setStep } =
    useReportStore();

  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const photoInputRef = useRef<HTMLInputElement>(null);
  const templateInputRef = useRef<HTMLInputElement>(null);

  const handlePhotoDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const files = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith("image/"));
      setPhotoFiles([...photoFiles, ...files]);
    },
    [photoFiles, setPhotoFiles],
  );

  const handlePhotoSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      setPhotoFiles([...photoFiles, ...files]);
    },
    [photoFiles, setPhotoFiles],
  );

  const removePhoto = useCallback(
    (idx: number) => setPhotoFiles(photoFiles.filter((_, i) => i !== idx)),
    [photoFiles, setPhotoFiles],
  );

  const handleSubmit = async () => {
    if (photoFiles.length === 0) { setError("Upload at least one photo"); return; }
    setError("");
    setUploading(true);
    try {
      const result = await uploadFiles(photoFiles, templateFile);
      setSessionId(result.session_id);
      setStep("processing");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12 animate-fade-up">
      {/* Theme toggle — top right */}
      <div className="fixed top-5 right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Hero */}
      <div className="flex items-center gap-2.5 mb-6">
        <img src="/logo-icon.png" alt="" className="h-10 dark:brightness-150" />
        <span
          style={{ fontFamily: "'Gveret Levin', cursive" }}
          className="text-4xl text-brand-600 dark:text-brand-400"
        >
          Vitruvius
        </span>
      </div>
      <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
        Add site photos to get started
      </p>

      {/* Content */}
      <div className="w-full max-w-md space-y-4">
        {/* Photo drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handlePhotoDrop}
          onClick={() => photoInputRef.current?.click()}
          className={`group rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-300 ${
            dragActive
              ? "border-brand-500 bg-brand-500/5 glow-brand"
              : "border-[var(--border)] hover:border-brand-400"
          }`}
        >
          <input ref={photoInputRef} type="file" multiple accept="image/*" onChange={handlePhotoSelect} className="hidden" />
          <div className="flex flex-col items-center gap-2">
            <svg className="w-8 h-8 text-brand-400 dark:text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Drop photos or <span className="text-brand-600 dark:text-brand-400 font-medium">browse</span>
            </p>
          </div>
        </div>

        {/* Thumbnails */}
        {photoFiles.length > 0 && (
          <div className="animate-fade-in">
            <p className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>
              {photoFiles.length} photo{photoFiles.length !== 1 && "s"}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {photoFiles.map((f, i) => (
                <div key={i} className="relative group w-12 h-12 rounded-lg overflow-hidden">
                  <img src={URL.createObjectURL(f)} alt={f.name} className="w-full h-full object-cover" />
                  <button
                    onClick={(e) => { e.stopPropagation(); removePhoto(i); }}
                    className="absolute inset-0 bg-black/0 group-hover:bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <span className="text-white text-xs">&times;</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Template */}
        <div
          onClick={() => templateInputRef.current?.click()}
          className="card card-hover rounded-xl px-4 py-3 cursor-pointer flex items-center gap-3"
        >
          <input ref={templateInputRef} type="file" accept=".docx,.doc,.pdf"
            onChange={(e) => setTemplateFile(e.target.files?.[0] || null)} className="hidden" />
          <svg className="w-4 h-4 shrink-0" style={{ color: "var(--text-muted)" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {templateFile ? (
            <span className="text-sm" style={{ color: "var(--text-primary)" }}>{templateFile.name}</span>
          ) : (
            <span className="text-sm" style={{ color: "var(--text-muted)" }}>
              Report template <span className="text-xs">(optional)</span>
            </span>
          )}
        </div>

        {/* Error */}
        {error && (
          <p className="text-sm text-red-500 text-center animate-fade-in">{error}</p>
        )}

        {/* Submit */}
        <div className="pt-2 flex justify-center">
          <button
            onClick={handleSubmit}
            disabled={uploading || photoFiles.length === 0}
            className="px-8 py-2.5 text-sm font-medium rounded-full bg-brand-600 text-white hover:bg-brand-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 active:scale-[0.97]"
          >
            {uploading ? (
              <span className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Uploading
              </span>
            ) : (
              "Create Report"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
