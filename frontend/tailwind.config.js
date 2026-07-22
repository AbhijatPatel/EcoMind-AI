/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        fog: "#EDEFE9", // page background — pale sage-grey, deliberately not warm cream
        bark: "#1F2B22", // primary ink / headings — deep forest-charcoal, not pure black
        paper: "#F7F8F4", // card surfaces, slightly lighter than fog
        verdigris: {
          DEFAULT: "#4C9A8B",
          dark: "#387D70",
          light: "#7DBCAF",
        },
        moss: "#5B8C7B",
        copper: "#B5673B", // raw / high-impact accent — unoxidized copper
        "copper-dark": "#8F4E2C",
        mist: "#C7CCC2", // borders, dividers, disabled states
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Work Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      borderRadius: {
        card: "1.25rem",
      },
    },
  },
  plugins: [],
};
