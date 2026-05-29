import { type ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "warning" | "danger" | "outline";
  size?: "sm" | "md";
}

const STYLES: Record<string, React.CSSProperties> = {
  primary:   { background: "#22C7C9", color: "#071D3A" },
  secondary: { background: "#F8FAFC", color: "#071D3A", border: "1px solid #D8E0EA" },
  warning:   { background: "#F59E0B", color: "white" },
  danger:    { background: "#E52920", color: "white" },
  outline:   { background: "transparent", color: "#1267D8", border: "1px solid #1267D8" },
};

export function ActionButton({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...rest
}: Props) {
  const base =
    "inline-flex items-center gap-1.5 font-medium rounded transition-colors focus:outline-none disabled:opacity-50";
  const sz = size === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";

  return (
    <button className={`${base} ${sz} ${className}`} style={STYLES[variant]} {...rest}>
      {children}
    </button>
  );
}
