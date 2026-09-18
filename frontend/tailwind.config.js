/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Design plan (see README "Design tokens"):
        // A data workbench, not a SaaS brochure — deep navy surfaces,
        // one warm amber accent for "opportunity", teal reserved
        // strictly for matched/positive signal so it stays meaningful.
        base: "#0E1424",       // page background
        surface: "#161E33",    // panels / rail
        surface2: "#1E2A47",   // raised elements (cards, inputs)
        line: "#2B3757",       // borders/dividers
        ink: "#EDEFF5",        // primary text
        muted: "#8C96B3",      // secondary text
        amber: "#E8A33D",      // primary accent (opportunity / CTA)
        "amber-dim": "#B9812C",
        teal: "#3FA796",       // positive / matched-skill signal only
        coral: "#D9636B",      // missing-skill / low-score signal only
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "10px",
        pill: "999px",
      },
    },
  },
  plugins: [],
};
