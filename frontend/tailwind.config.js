export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-red': '#E30613',
        'trainmore-dark': '#000000',
        'industrial-gray': '#1A1A1A',
      },
      boxShadow: {
        'glow': '0 0 15px rgba(227, 6, 19, 0.4)',
      },
      fontFamily: {
        'industrial': ['Oswald', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
