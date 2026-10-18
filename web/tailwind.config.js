/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // "Sage & Clay" theme (approved in the Claude canvas): cream, sage green, clay, butter.
        ink: "#2b3a2f",
        ivory: "#fffaf1",
        sage: "#dcebd6",
        clay: "#b4421d",
        brand: {
          300: "#2f5a3a",
          400: "#3f6b4a",
          500: "#3f6b4a",
          600: "#3f6b4a",
          700: "#2f5a3a",
          900: "#dcebd6",
        },
        surface: {
          500: "#8d9686",
          600: "#d9ccb2",
          700: "#efe6d3",
          800: "#fffaf1",
          900: "#f6efe3",
        },
        // Text shades darkened so they stay AA-readable on the cream surfaces.
        slate: { 200: "#26332a", 300: "#34443a", 400: "#4a5a4d", 500: "#66756a" },
        red: { 300: "#a8381a", 400: "#a8381a" },
        amber: { 300: "#7a5600", 400: "#7a5600" },
        emerald: { 300: "#2f5a3a", 400: "#2f5a3a" },
        green: { 300: "#2f5a3a", 400: "#2f5a3a" },
        blue: { 400: "#1d4d5c" },
        purple: { 400: "#6b3a8a" },
        orange: { 400: "#a24a06" },
      },
      fontFamily: {
        sans: ['"Inter"', '"Heebo"', "system-ui", "-apple-system", "sans-serif"],
        serif: ['"Iowan Old Style"', '"Palatino Linotype"', "Palatino", "Georgia", '"David"', '"Times New Roman"', "serif"],
      },
      borderRadius: { lg: "0.75rem", xl: "1rem", "2xl": "1.375rem" },
      boxShadow: {
        card: "0 1px 0 0 rgb(43 58 47 / 0.04)",
      },
    },
  },
  plugins: [],
};