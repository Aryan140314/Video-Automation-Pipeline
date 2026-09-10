/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        studio: {
          900: "#090d16",
          800: "#0f172a",
          700: "#1e293b",
          600: "#334155",
          500: "#64748b",
          accent: "#6366f1",
          glow: "#818cf8",
          neon: "#a855f7",
          cyan: "#06b6d4"
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"]
      }
    },
  },
  plugins: [],
}
