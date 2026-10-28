# AGENTS.md — Mind2Code frontend

## Structure

- Vue 3 (`<script setup>`) + Vite + Vue Router + Tailwind v3 + axios + lucide.
- `src/App.vue` — shell: `AppHeader` + `RouterView` + `ToastHost`.
- `src/views/` — one file per route; `src/components/` — feature components;
  `src/components/ui/` — reusable primitives (badge, field, bottom sheet, ...).
- `src/services/api.js` — the only place that talks HTTP.
- `src/composables/` — `useToast` (module-level singleton), `useMediaQuery`.
- `src/utils/` — `format.js` (money/number/date/pct), `trend.js`.
- `orbit-ecosystem-preset.js` — shared Orbit dark theme; used via
  `tailwind.config.js` `presets`. Do not edit per project.

## Commands

- Dev: `npm run dev` (Vite, http://localhost:5173)
- Build: `npm run build` (outputs `dist/`)
- Lint: `npm run lint` (oxlint + eslint, with `--fix`)
- Format: `npm run format` (prettier)

## Conventions

- **Mobile-first.** Design at the base breakpoint, enhance with `lg:`. Use
  `env(safe-area-inset-*)` for spacing that touches the screen edges.
- **Cards** use `.app-card rounded-app p-5` (gradient border + blur, defined in
  `src/style.css`).
- Use the `brand-*` tokens only (`bg-brand-background`, `bg-brand-surface`,
  `text-brand-textMain`, `text-brand-textMuted`, `bg-brand-primary`,
  `bg-brand-secondary`). Never hardcode theme colors.
- One component per file; props via `defineProps`, events via `defineEmits`.
- API calls go through `src/services/api.js`; components never import axios.
- Non-initial routes are lazy-loaded.
- Cross-component UI state is a module-level singleton composable (`useToast`).

## Notes

- `@` is an alias for `src/` (see `vite.config.js` / `jsconfig.json`).
- `assetsDir` is `static` (not `assets`) to avoid clashing with a possible
  `/assets` SPA route; `nginx.conf` caches `/static/`.
- PWA: `index.html` + `public/manifest.json`; replace the placeholder icons in
  `public/` with the real logo.
- For UI conventions in depth, use the `vue-orbit-ui` skill; for a new project
  from scratch use `vue-orbit-scaffold`.
