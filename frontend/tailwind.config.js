/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
         // Custom accents if needed, otherwise use Zinc
         brand: {
             50: '#f0f9ff',
             500: '#0ea5e9', // Sky blue for primary actions
             600: '#0284c7',
             900: '#0c4a6e',
         }
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, #f4f4f5 1px, transparent 1px), linear-gradient(to bottom, #f4f4f5 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
}
