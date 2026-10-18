/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // "Forest Fleet" theme (custom, from theme-factory's Forest Canopy family): green, ivory, terracotta.
        ink: "#1c2a1a",
        forest: "#233d22",
        ivory: "#faf7ee",
        accent: "#a8481f",
        brand: {
          300: "#2d4a2b",
          400: "#2f5a2c",
          500: "#2f5a2c",
          600: "#2d4a2b",
          700: "#1f3a1e",
          900: "#cfdcc8",
        },
        surface: {
          500: "#8a8f78",
          600: "#cdc6ad",
          700: "#ebe5d3",
          800: "#fffdf7",
          900: "#f4f0e4",
        },
        // Text shades darkened so they stay AA-readable on light surfaces.
        slate: { 200: "#232f21", 300: "#33402f", 400: "#4d5a47", 500: "#687362" },
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
        serif: ['"Iowan Old Style"', '"Palatino Linotype"', "Palatino", "Georgia", '"David"', '"Times New Roman"', "serif"],
      },
      borderRadius: { lg: "0.375rem", xl: "0.5rem", "2xl": "0.625rem" },
      boxShadow: {
        card: "0 1px 0 0 rgb(45 74 43 / 0.06)",
      },
    },
  },
  plugins: [],
};