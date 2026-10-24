import orbitEcosystemPreset from './orbit-ecosystem-preset'

/** @type {import('tailwindcss').Config} */
export default {
  presets: [orbitEcosystemPreset],
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
}
