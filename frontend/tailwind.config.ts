import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#071D3A",
          2: "#09294D",
          3: "#0D3560",
        },
        teal: "#22C7C9",
        "brand-blue": "#1267D8",
        "brand-orange": "#F59E0B",
        "brand-red": "#E52920",
        canvas: "#F8FAFC",
        line: "#D8E0EA",
        muted: "#667085",
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "system-ui", "-apple-system", "sans-serif"],
        mono: ["DM Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card:   "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)",
        "card-hover": "0 0 0 1px #CDD5E0, 0 2px 8px 0 rgb(7 29 58 / 0.09)",
        dropdown: "0 0 0 1px #E8EDF3, 0 4px 16px 0 rgb(7 29 58 / 0.12)",
        "inset-focus": "inset 0 0 0 2px #22C7C9",
      },
      keyframes: {
        "pulse-ring": {
          "0%":   { transform: "scale(1)",    opacity: "1" },
          "70%":  { transform: "scale(2.2)",  opacity: "0.15" },
          "100%": { transform: "scale(2.2)",  opacity: "0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 2s ease-out infinite",
        "fade-in":    "fade-in 0.2s ease-out both",
        "slide-up":   "slide-up 0.25s cubic-bezier(0.22,1,0.36,1) both",
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.22, 1, 0.36, 1)",
        "in-out-quart": "cubic-bezier(0.76, 0, 0.24, 1)",
      },
      transitionDuration: {
        "120": "120ms",
        "160": "160ms",
      },
    },
  },
  plugins: [],
};

export default config;
