/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'royal': '#075985',  // Royal blue
        'light': '#e0f2fe',  // Light blue
        'accent': '#dc2626', // Red accent
      }
    },
  },
  plugins: [],
}

