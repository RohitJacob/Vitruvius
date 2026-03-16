interface PhotoCardProps {
  photoId: string;
  b64: string;
  mime: string;
  isKey: boolean;
  filename?: string;
  onToggleKey?: () => void;
  onMoveOut?: () => void;
  selected?: boolean;
  onSelect?: () => void;
}

export default function PhotoCard({
  b64, mime, isKey, filename, onToggleKey, onMoveOut, selected, onSelect,
}: PhotoCardProps) {
  const src = `data:${mime};base64,${b64}`;

  return (
    <div
      onClick={onSelect}
      className={`relative group rounded-xl overflow-hidden cursor-pointer transition-all duration-200 ring-1 ${
        selected
          ? "ring-brand-500 shadow-lg shadow-brand-500/10"
          : isKey
            ? "ring-brand-500/30"
            : "ring-[var(--border)] hover:ring-brand-300 dark:hover:ring-brand-500/30"
      }`}
    >
      <img src={src} alt={filename || "Site photo"} className="w-full aspect-square object-cover" loading="lazy" />

      {isKey && (
        <span className="absolute top-1.5 left-1.5 bg-brand-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-md tracking-wide">
          KEY
        </span>
      )}

      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-all duration-200 flex items-end justify-between">
        {onToggleKey && (
          <button
            onClick={(e) => { e.stopPropagation(); onToggleKey(); }}
            className="text-[10px] bg-white/15 backdrop-blur-sm text-white px-2 py-0.5 rounded-md font-medium hover:bg-white/25 transition-colors"
          >
            {isKey ? "Unset" : "Key"}
          </button>
        )}
        {onMoveOut && (
          <button
            onClick={(e) => { e.stopPropagation(); onMoveOut(); }}
            className="text-[10px] bg-white/15 backdrop-blur-sm text-white px-2 py-0.5 rounded-md font-medium hover:bg-white/25 transition-colors"
          >
            Separate
          </button>
        )}
      </div>

      {filename && (
        <div className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="bg-black/60 backdrop-blur-sm text-white text-[9px] px-1.5 py-0.5 rounded-md max-w-[100px] truncate block">
            {filename}
          </span>
        </div>
      )}
    </div>
  );
}
