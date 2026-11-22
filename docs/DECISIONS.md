# Architecture decisions

## Frontend: Vite and React

The UI uses Vite with React 18+ and TypeScript in strict mode. Vite gives fast local development and a straightforward production build. React Router handles screen navigation without a full page reload. TanStack Query manages API loading and caching against the backend under `/api/...`.

## Plain CSS and design tokens

The interface uses hand-written CSS split into tokens, base, layout, and components. Tailwind and third-party UI kits were avoided so contrast, touch targets, and typography stay predictable for older adults. Colours and spacing live in `frontend/src/styles/tokens.css` and are checked by `scripts/check_contrast.ts` and Vitest.

## Optional map (Leaflet)

The Scams near me screen can show an OpenStreetMap view via `react-leaflet`. The map is lazy-loaded and hidden by default so the page works without map tiles or JavaScript map support. Reports do not depend on the map.

## PWA and offline help

`vite-plugin-pwa` registers a service worker. Help now content is cached with a network-first strategy so basic steps remain available when offline after a prior visit.

## Copy and accessibility

All user-facing strings are in `frontend/src/strings.ts` in plain British English. Persistent error banners use a Close control. Skip link and focus outlines follow WCAG-oriented patterns. Automated checks include `vitest-axe` on the home screen and contrast ratio tests on design tokens.