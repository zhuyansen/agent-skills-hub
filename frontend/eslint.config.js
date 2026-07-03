import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";

export default defineConfig([
  globalIgnores(["dist"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Underscore prefix = intentionally-unused (destructured props kept for
      // documentation, e.g. `_onSelect`). Codebase-wide convention.
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      // react-hooks v7 additions, downgraded error → warn (2026-07-03):
      // - set-state-in-effect flags the STANDARD fetch pattern
      //   (setLoading(true) at effect start) at 24 sites. The "fix" is
      //   adopting react-query/useSyncExternalStore across the app — an
      //   ocean, not a lake. Keep visible as warnings for future refactors.
      // - immutability false-positives on `window.location.href = …` hard
      //   navigation (SiteFooter → static /blog/ page).
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/immutability": "warn",
      // HMR-only concern; exporting helpers alongside components (ScoreBadge
      // tier fns, context hooks) is deliberate. Not a production issue.
      "react-refresh/only-export-components": "warn",
    },
  },
]);
