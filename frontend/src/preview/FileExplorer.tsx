interface Props {
  files: Record<string, string>
  selectedFile: string | null
  onSelect: (filename: string) => void
}

const ICON_MAP: Record<string, string> = {
  ".py": "py",
  ".txt": "txt",
  ".json": "json",
  ".yaml": "yml",
  ".yml": "yml",
  ".md": "md",
}

function getFileIcon(filename: string): string {
  const ext = filename.slice(filename.lastIndexOf("."))
  return ICON_MAP[ext] ?? "file"
}

export function FileExplorer({ files, selectedFile, onSelect }: Props) {
  const filenames = Object.keys(files).sort((a, b) => {
    // main.py first, then alphabetical
    if (a === "main.py") return -1
    if (b === "main.py") return 1
    return a.localeCompare(b)
  })

  return (
    <div className="overflow-y-auto">
      <div className="px-3 py-2 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider">
        Files
      </div>
      {filenames.map((name) => (
        <button
          key={name}
          onClick={() => onSelect(name)}
          className={`w-full text-left px-3 py-1.5 text-[12px] font-mono flex items-center gap-2 transition-colors ${
            selectedFile === name
              ? "bg-accent/10 text-accent border-l-2 border-accent"
              : "text-text-secondary hover:bg-surface-elevated hover:text-text-primary border-l-2 border-transparent"
          }`}
        >
          <span className="text-[10px] text-text-tertiary w-5 text-center shrink-0">
            {getFileIcon(name)}
          </span>
          <span className="truncate">{name}</span>
        </button>
      ))}
    </div>
  )
}
