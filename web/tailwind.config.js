/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          300: "#a5b8ff",
          400: "#8aa2ff",
          500: "#6482fb",
          600: "#4361ee",
          700: "#3451d1",
          900: "#1b2a6b",
        },
        surface: {
          500: "#5a6690",
          600: "#2b3759",
          700: "#1d2845",
          800: "#131c33",
          900: "#0b1120",
        },
      },
      fontFamily: {
        sans: ['"Inter"', '"Heebo"', "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: { xl: "0.875rem", "2xl": "1.125rem" },
      boxShadow: {
        card: "0 1px 0 0 rgb(255 255 255 / 0.03) inset, 0 8px 24px -12px rgb(0 0 0 / 0.55)",
      },
    },
  },
  plugins: [],
};