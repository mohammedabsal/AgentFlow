const config = {
  content: ['./src/**/*.{ts,tsx}'],
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        bg: 'hsl(var(--bg))',
        panel: 'hsl(var(--panel))',
        line: 'hsl(var(--line))',
        text: 'hsl(var(--text))',
        muted: 'hsl(var(--muted))',
        accent: 'hsl(var(--accent))',
        accent2: 'hsl(var(--accent2))',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(255,255,255,0.06), 0 24px 80px rgba(15,23,42,0.45)',
      },
      backgroundImage: {
        'grid-fade': 'radial-gradient(circle at top, rgba(94,234,212,0.18), transparent 35%), linear-gradient(180deg, rgba(2,6,23,1), rgba(15,23,42,1))',
      },
    },
  },
  plugins: [],
};

export default config;
