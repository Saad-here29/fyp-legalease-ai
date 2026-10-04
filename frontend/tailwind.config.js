/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
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
      },
      fontFamily: {
        // Design system v1: Newsreader for identity + page/section titles,
        // IBM Plex Sans for everything you work in.
        "ds-serif": ["Newsreader", "Georgia", "'Times New Roman'", "serif"],
        "ds-sans": ["'IBM Plex Sans'", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      typography: ({ theme }) => ({
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
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
