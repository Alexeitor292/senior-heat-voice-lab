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
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
