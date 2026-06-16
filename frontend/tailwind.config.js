// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: 'hsl(210, 80%, 55%)',
        danger: 'hsl(0, 80%, 55%)',
        success: 'hsl(120, 70%, 45%)',
      },
    },
  },
  plugins: [],
};
