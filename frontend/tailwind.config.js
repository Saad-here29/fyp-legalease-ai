/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        legal: {
          gold: "#C9A961",
          navy: "#0B1B2B",
          ink: "#0E1726",
          mist: "#F4F1EA",
        },
        // ===== New editorial design system (2026 redesign) =====
        // Rolled out one page at a time — see docs/STYLE_GUIDE.md.
        // Additive only: none of the tokens above are touched, so pages not
        // yet converted keep looking exactly as they did before.
        // 2026-09 overhaul: same paper/ink identity, higher contrast. On
        // paper: ink-text 16.0:1, ink-muted 7.9:1 (was 5.3), brick 7.2:1.
        paper: "#F6F1E7",
        "ink-panel": "#1E2E28",
        "ink-text": "#1A1611",
        "ink-muted": "#51493E",
        hairline: "#B5A88B",
        "hairline-subtle": "#DCD1BA",
        // Accent and "urgent" status intentionally share this hex — see
        // docs/STYLE_GUIDE.md for why. Use `brick` for both.
        brick: "#8A3324",
        "status-active": "#3E6E52",
        // ===== Design system v1 (docs/design_reference, page 1) =====
        // Prefixed `ds-` so pages migrate one at a time: `paper` above is
        // #F6F1E7 and the spec's Paper is #F4EFE4, so redefining shared names
        // would shift every unmigrated page at once. Measured contrast on
        // Paper: text 14.6:1, text-2 7.3:1, seal 6.5:1, pass 7.6:1,
        // review 5.5:1; white on seal 7.5:1.
        ds: {
          ink: "#0F2A22",       // identity panels, sidebar, section rules
          "ink-2": "#173A2F",   // raised areas on ink, active pill
          paper: "#F4EFE4",     // page background
          sheet: "#FBF8F2",     // documents, ledgers, inputs
          rule: "#D9D0BD",      // hairlines, borders
          text: "#14201A",      // headings and body
          "text-2": "#45504A",  // secondary, labels
          seal: "#9E2B1D",      // the one accent: "act here"
          pass: "#17553A",      // checks that pass, verified
          review: "#8A5300",    // needs a human look
          // Tints and states sampled from the page-1 component row
          "pass-tint": "#DEEBE1",
          "seal-tint": "#F4E1DA",
          "review-tint": "#F6E8CD",
          disabled: "#E6DFCF",
          underline: "#C7BBA5",
        },
        "status-pending": "#B08B3C",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["'Playfair Display'", "Georgia", "serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
        // New design system's heading/identity-moment serif — deliberately
        // separate from `serif` above (Playfair Display) so existing pages
        // using `font-serif` are unaffected until they're redesigned too.
        editorial: ["Georgia", "'Times New Roman'", "serif"],
        // Design system v1: Newsreader for identity + page/section titles,
        // IBM Plex Sans for everything you work in.
        "ds-serif": ["Newsreader", "Georgia", "'Times New Roman'", "serif"],
        "ds-sans": ["'IBM Plex Sans'", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      // `prose prose-ink`: the single style for ALL AI-generated content
      // (chat answers, document summaries, contract text).
      typography: ({ theme }) => ({
        ink: {
          css: {
            "--tw-prose-body": theme("colors.ink-text"),
            "--tw-prose-headings": theme("colors.ink-text"),
            "--tw-prose-lead": theme("colors.ink-muted"),
            "--tw-prose-links": theme("colors.brick"),
            "--tw-prose-bold": theme("colors.ink-text"),
            "--tw-prose-counters": theme("colors.brick"),
            "--tw-prose-bullets": theme("colors.brick"),
            "--tw-prose-hr": theme("colors.hairline-subtle"),
            "--tw-prose-quotes": theme("colors.ink-text"),
            "--tw-prose-quote-borders": theme("colors.brick"),
            "--tw-prose-captions": theme("colors.ink-muted"),
            "--tw-prose-code": theme("colors.ink-text"),
            "--tw-prose-th-borders": theme("colors.hairline"),
            "--tw-prose-td-borders": theme("colors.hairline-subtle"),
            // AI answers use ###-level headings: keep them sans and modest
            // so they structure the answer without shouting over the page's
            // own serif headings.
            "h1, h2, h3, h4": { fontFamily: theme("fontFamily.sans").join(", "), fontWeight: "600" },
            h1: { fontSize: "1.375em" },
            h2: { fontSize: "1.25em" },
            h3: { fontSize: "1.125em", marginTop: "1.5em", marginBottom: "0.5em" },
            a: { textUnderlineOffset: "3px" },
            "thead th": { color: theme("colors.ink-muted"), fontWeight: "600" },
            "sup.citation-marker": { color: theme("colors.brick"), fontWeight: "600" },
          },
        },
        // Design system v1 reading style for AI output (`prose prose-ds`):
        // Plex Sans throughout, ink table rule under the header row, hairline
        // row dividers, list markers in Text 2 (Seal is never decoration).
        ds: {
          css: {
            "--tw-prose-body": theme("colors.ds.text"),
            "--tw-prose-headings": theme("colors.ds.text"),
            "--tw-prose-lead": theme("colors.ds.text-2"),
            "--tw-prose-links": theme("colors.ds.text"),
            "--tw-prose-bold": theme("colors.ds.text"),
            "--tw-prose-counters": theme("colors.ds.text-2"),
            "--tw-prose-bullets": theme("colors.ds.text-2"),
            "--tw-prose-hr": theme("colors.ds.rule"),
            "--tw-prose-quotes": theme("colors.ds.text"),
            "--tw-prose-quote-borders": theme("colors.ds.rule"),
            "--tw-prose-captions": theme("colors.ds.text-2"),
            "--tw-prose-code": theme("colors.ds.text"),
            "--tw-prose-th-borders": theme("colors.ds.ink"),
            "--tw-prose-td-borders": theme("colors.ds.rule"),
            fontFamily: theme("fontFamily.ds-sans").join(", "),
            fontSize: "17px",
            lineHeight: "28px",
            "h1, h2, h3, h4": { fontFamily: theme("fontFamily.ds-sans").join(", "), fontWeight: "600" },
            h1: { fontSize: "24px", lineHeight: "32px", marginTop: "1.4em", marginBottom: "0.5em" },
            h2: { fontSize: "21px", lineHeight: "30px", marginTop: "1.4em", marginBottom: "0.5em" },
            h3: { fontSize: "19px", lineHeight: "28px", marginTop: "1.6em", marginBottom: "0.5em" },
            h4: { fontSize: "17px", lineHeight: "28px" },
            "h1:first-child, h2:first-child, h3:first-child": { marginTop: "0" },
            a: {
              fontWeight: "600",
              textDecorationColor: theme("colors.ds.underline"),
              textDecorationThickness: "2px",
              textUnderlineOffset: "5px",
            },
            table: { fontSize: "16px", lineHeight: "24px" },
            "thead th": { color: theme("colors.ds.text-2"), fontWeight: "600", fontSize: "15px", paddingBottom: "12px" },
            thead: { borderBottomWidth: "2px" },
            "tbody td": { paddingTop: "14px", paddingBottom: "14px" },
          },
        },
      }),
      maxWidth: {
        "ds-content": "1064px",   // content column max
      },
      borderRadius: {
        ds: "4px",                 // corners are 2-4px
        "ds-sm": "2px",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      backgroundImage: {
        "legal-gradient":
          "linear-gradient(135deg, #0B1B2B 0%, #0E1726 50%, #1A2740 100%)",
        "gold-gradient":
          "linear-gradient(135deg, #C9A961 0%, #E5C880 50%, #C9A961 100%)",
        "glass": "linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.4s ease-out",
        "shimmer": "shimmer 2s linear infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
};
