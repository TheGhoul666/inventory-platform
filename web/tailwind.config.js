/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        brand: {
          300: "#2f49c9",
          400: "#3a55e0",
          500: "#3d58df",
          600: "#4361ee",
          700: "#3451d1",
          900: "#c9d3fb",
        },
        // Light theme: the former "dark" surface scale, inverted.
        surface: {
          500: "#8693b3",
          600: "#c9d2e6",
          700: "#e6ebf5",
          800: "#ffffff",
          900: "#f1f4fa",
        },
        // Text shades darkened so they stay AA-readable on light surfaces.
        slate: { 200: "#1e293b", 300: "#334155", 400: "#475569", 500: "#64748b" },
        red: { 300: "#dc2626", 400: "#b91c1c" },
        amber: { 300: "#b45309", 400: "#a24a06" },
        emerald: { 300: "#047857", 400: "#047857" },
        green: { 300: "#15803d", 400: "#15803d" },
        blue: { 400: "#1d4ed8" },
        purple: { 400: "#7e22ce" },
        orange: { 400: "#c2410c" },
      },
      fontFamily: {
        sans: ['"Inter"', '"Heebo"', "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: { xl: "0.875rem", "2xl": "1.125rem" },
      boxShadow: {
        card: "0 1px 2px 0 rgb(16 24 40 / 0.05), 0 10px 28px -14px rgb(16 24 40 / 0.18)",
      },
    },
  },
  plugins: [],
};