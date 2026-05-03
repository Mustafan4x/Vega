// Trader · Oxblood · Tailwind theme.extend snippet
// Source of truth: /home/mustafa/src/trader/docs/design/claude-design-output.html
// (specifically the JSON `tailwindSketch` inside <script type="application/json" id="design-manifest">).
//
// DevOps: drop the object below into `frontend/tailwind.config.ts` under
// `theme.extend`. All colors reference the CSS variables defined at `:root`
// in the canonical HTML and mirrored in `frontend/src/index.css`.

export const oxbloodThemeExtend = {
  colors: {
    primary: {
      50: "var(--color-primary-50)",
      100: "var(--color-primary-100)",
      200: "var(--color-primary-200)",
      300: "var(--color-primary-300)",
      400: "var(--color-primary-400)",
      500: "var(--color-primary-500)",
      600: "var(--color-primary-600)",
      700: "var(--color-primary-700)",
      800: "var(--color-primary-800)",
      900: "var(--color-primary-900)",
      soft: "var(--color-primary-soft)",
      DEFAULT: "var(--color-primary-500)",
    },
    accent: {
      50: "var(--color-accent-50)",
      100: "var(--color-accent-100)",
      200: "var(--color-accent-200)",
      300: "var(--color-accent-300)",
      400: "var(--color-accent-400)",
      500: "var(--color-accent-500)",
      600: "var(--color-accent-600)",
      700: "var(--color-accent-700)",
      800: "var(--color-accent-800)",
      900: "var(--color-accent-900)",
      DEFAULT: "var(--color-accent-500)",
    },
    success: {
      50: "var(--color-success-50)",
      500: "var(--color-success-500)",
      700: "var(--color-success-700)",
      soft: "var(--color-success-soft)",
      DEFAULT: "var(--color-success-500)",
    },
    danger: {
      50: "var(--color-danger-50)",
      500: "var(--color-danger-500)",
      700: "var(--color-danger-700)",
      soft: "var(--color-danger-soft)",
      DEFAULT: "var(--color-danger-500)",
    },
    info: {
      50: "var(--color-info-50)",
      500: "var(--color-info-500)",
      700: "var(--color-info-700)",
      DEFAULT: "var(--color-info-500)",
    },
    neutral: {
      50: "var(--color-neutral-50)",
      100: "var(--color-neutral-100)",
      200: "var(--color-neutral-200)",
      300: "var(--color-neutral-300)",
      400: "var(--color-neutral-400)",
      500: "var(--color-neutral-500)",
      600: "var(--color-neutral-600)",
      700: "var(--color-neutral-700)",
      800: "var(--color-neutral-800)",
      900: "var(--color-neutral-900)",
    },
    background: "var(--color-background)",
    surface: "var(--color-surface)",
    "surface-2": "var(--color-surface-2)",
    border: "var(--color-border)",
    fg: "var(--color-text-primary)",
    "fg-muted": "var(--color-text-muted)",
    "fg-subtle": "var(--color-text-subtle)",
    "fg-inverse": "var(--color-text-inverse)",
    "greek-amber": "var(--color-greek-amber)",
    "greek-violet": "var(--color-greek-violet)",
  },
  fontFamily: {
    sans: ["Manrope", "Inter", "system-ui", "sans-serif"],
    display: ["IBM Plex Serif", "Georgia", "serif"],
    number: ["Newsreader", "Iowan Old Style", "Georgia", "serif"],
    mono: ["JetBrains Mono", "ui-monospace", "Menlo", "monospace"],
  },
  fontSize: {
    "display-lg": ["56px", { lineHeight: "1.05" }],
    "display-md": ["32px", { lineHeight: "1.05" }],
    "heading-lg": ["24px", { lineHeight: "1.2" }],
    "heading-md": ["19px", { lineHeight: "1.25" }],
    "body-lg": ["17px", { lineHeight: "1.5" }],
    "body-md": ["15px", { lineHeight: "1.5" }],
    "body-sm": ["14px", { lineHeight: "1.5" }],
    caption: ["13px", { lineHeight: "1.4" }],
    micro: ["11px", { lineHeight: "1.3" }],
  },
  fontWeight: {
    regular: "400",
    medium: "500",
    semibold: "600",
    bold: "700",
  },
  letterSpacing: {
    tight: "-0.01em",
    normal: "0",
    wide: "0.04em",
    caps: "0.06em",
  },
  spacing: {
    0: "0px",
    1: "4px",
    2: "8px",
    3: "12px",
    4: "16px",
    5: "20px",
    6: "24px",
    7: "32px",
    8: "40px",
    10: "56px",
    12: "72px",
    16: "96px",
  },
  borderRadius: {
    sm: "3px",
    md: "6px",
    lg: "10px",
    card: "6px",
    pill: "999px",
  },
  boxShadow: {
    sm: "0 1px 2px rgba(0,0,0,0.25)",
    md: "0 4px 12px rgba(0,0,0,0.30)",
    card: "0 1px 2px rgba(0,0,0,0.25), 0 6px 16px rgba(0,0,0,0.28)",
    "card-hover": "0 1px 2px rgba(0,0,0,0.25), 0 12px 28px rgba(0,0,0,0.40)",
    focus: "0 0 0 3px var(--color-primary-soft)",
  },
  transitionDuration: {
    fast: "100ms",
    base: "180ms",
    slow: "320ms",
  },
  transitionTimingFunction: {
    standard: "cubic-bezier(0.2, 0, 0, 1)",
    emphasized: "cubic-bezier(0.22, 0.8, 0.36, 1)",
  },
  zIndex: {
    popover: "20",
    modal: "40",
  },
  maxWidth: {
    page: "1400px",
  },
  width: {
    sidebar: "232px",
  },
  height: {
    topbar: "56px",
  },
} as const;

// Usage in frontend/tailwind.config.ts:
//
//   import { oxbloodThemeExtend } from "../docs/design/tailwind-extension.snippet";
//   export default {
//     content: ["./index.html", "./src/**/*.{ts,tsx}"],
//     theme: { extend: oxbloodThemeExtend },
//     plugins: [],
//   } satisfies Config;
//
// Or paste the literal object inline under `theme.extend` if the Frontend
// Developer prefers not to import from outside the frontend/ tree.
