# Mind2Code — Frontend

Project dashboard SPA

Vue 3 + Vite + Tailwind CSS single-page app using the shared **Orbit Ecosystem**
dark theme.

## Tech stack

| Technology | Notes |
| --- | --- |
| Vue 3 | `<script setup>`, Composition API |
| Vite | Dev server + build |
| Vue Router | Client-side routing |
| Tailwind CSS v3 | via `orbit-ecosystem-preset.js` |
| axios | HTTP client (see `src/services/api.js`) |
| lucide | Icons |
| oxlint + eslint + prettier | Lint / format |

## Project structure

```
src/
├── main.js              # createApp + router
├── App.vue              # shell (header, router view, navbar, toasts)
├── style.css            # Tailwind layers + .app-card + helpers
├── router/index.js
├── services/api.js
├── composables/{useToast,useMediaQuery}.js
├── components/
│   ├── AppHeader.vue
│   ├── AppNavbar.vue
│   └── ui/              # reusable primitives
└── views/
```

## Development

```sh
npm install
npm run dev            # http://localhost:5173
```

`VITE_API_BASE_URL` comes from `.env` / `.env.development` (see `.env.example`).

## Build

```sh
npm run build          # -> dist/
npm run lint
```

## Docker

```sh
docker buildx build --platform linux/amd64 \
  --build-arg VITE_API_BASE_URL=https://api.example.com \
  -t registry/mind2code_fe:0.1.0 .
```

The image builds the app and serves `dist/` with nginx (SPA fallback configured
in `nginx.conf`). The API URL is inlined at build time, so it must be passed as a
build arg.
