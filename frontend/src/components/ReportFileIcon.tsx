interface Props {
  fileType: string;
  size?: number;
  showLabel?: boolean;
}

const TYPE_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  pdf: { bg: "#fee2e2", color: "#dc2626", label: "PDF" },
  csv: { bg: "#dcfce7", color: "#16a34a", label: "CSV" },
  xlsx: { bg: "#dcfce7", color: "#15803d", label: "XLSX" },
  xls: { bg: "#dcfce7", color: "#15803d", label: "XLS" },
  docx: { bg: "#dbeafe", color: "#2563eb", label: "DOCX" },
  txt: { bg: "#f1f5f9", color: "#475569", label: "TXT" },
};

function iconPath(type: string): string {
  switch (type) {
    case "pdf":
      return "M7 2h7l5 5v15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm7 0v5h5";
    case "csv":
    case "xlsx":
    case "xls":
      return "M4 4h16v16H4V4zm4 4v8m4-8v8m4-8v8";
    case "docx":
      return "M6 4h9l5 5v11H6V4zm9 0v5h5M8 13h8M8 17h6";
    default:
      return "M6 4h12v16H6V4zm2 4h8m-8 4h8";
  }
}

export default function ReportFileIcon({ fileType, size = 48, showLabel = true }: Props) {
  const key = fileType.toLowerCase();
  const style = TYPE_STYLES[key] ?? { bg: "#e2e8f0", color: "#64748b", label: key.toUpperCase() };

  return (
    <div
      className="report-file-icon"
      style={{ width: size, height: size, background: style.bg, color: style.color }}
      aria-hidden
      title={style.label}
    >
      <svg width={size * 0.5} height={size * 0.5} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
        <path d={iconPath(key)} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {showLabel && <span className="report-file-icon-label">{style.label}</span>}
    </div>
  );
}

export function categoryLabel(fileType: string): string {
  return TYPE_STYLES[fileType.toLowerCase()]?.label ?? fileType.toUpperCase();
}
