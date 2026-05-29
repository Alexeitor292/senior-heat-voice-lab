import { type ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "warning" | "danger" | "outline";
  size?: "sm" | "md";
}

const BASE_STYLES: Record<string, React.CSSProperties> = {
  primary:   { background: "#22C7C9", color: "#071D3A",  border: "1px solid rgba(0,0,0,0.06)" },
  secondary: { background: "#F8FAFC", color: "#374151",  border: "1px solid #E2E8F0" },
  warning:   { background: "#F59E0B", color: "white",    border: "1px solid rgba(0,0,0,0.06)" },
  danger:    { background: "#E52920", color: "white",    border: "1px solid rgba(0,0,0,0.06)" },
  outline:   { background: "transparent", color: "#1267D8", border: "1px solid #BFD5F5" },
};

const HOVER_STYLES: Record<string, React.CSSProperties> = {
  primary:   { background: "#1DB8BA", boxShadow: "0 1px 4px rgba(34,199,201,0.3)" },
  secondary: { background: "#F1F5F9", borderColor: "#CDD5E0" },
  warning:   { background: "#E08E0A", boxShadow: "0 1px 4px rgba(245,158,11,0.3)" },
  danger:    { background: "#C8221A", boxShadow: "0 1px 4px rgba(229,41,32,0.3)" },
  outline:   { background: "#EFF6FF", borderColor: "#93B9EA" },
};

export function ActionButton({
  variant = "primary",
  size = "md",
  className = "",
  children,
  style,
  onMouseEnter,
  onMouseLeave,
  onMouseDown,
  onMouseUp,
  ...rest
}: Props) {
  const base =
    "inline-flex items-center gap-1.5 font-semibold rounded-md transition-interactive focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed";
  const sz = size === "sm"
    ? "px-3 py-1.5 text-xs"
    : "px-4 py-2 text-sm";

  return (
    <button
      className={`${base} ${sz} ${className}`}
      style={{ ...BASE_STYLES[variant], letterSpacing: "-0.005em", ...style }}
      onMouseEnter={(e) => {
        if (!rest.disabled) {
          Object.assign((e.currentTarget as HTMLElement).style, HOVER_STYLES[variant]);
        }
        onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        if (!rest.disabled) {
          const el = e.currentTarget as HTMLElement;
          Object.assign(el.style, BASE_STYLES[variant]);
          el.style.boxShadow = "";
          el.style.transform = "";
        }
        onMouseLeave?.(e);
      }}
      onMouseDown={(e) => {
        if (!rest.disabled) {
          (e.currentTarget as HTMLElement).style.transform = "scale(0.975)";
        }
        onMouseDown?.(e);
      }}
      onMouseUp={(e) => {
        if (!rest.disabled) {
          (e.currentTarget as HTMLElement).style.transform = "";
        }
        onMouseUp?.(e);
      }}
      {...rest}
    >
      {children}
    </button>
  );
}
