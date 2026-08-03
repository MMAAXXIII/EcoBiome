export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ecobiome: {
          background: "#010E16",
          surface: "#04161F",
          surfaceAlt: "#0B1B27",
          accent: "#6EE06A",
          accentSoft: "#7BF48A",
          amber: "#F7B955",
          coral: "#FF7E6B",
          border: "#0E1F2B",
          text: "#F3F7F4"
        }
      },
      boxShadow: {
        glow: "0 24px 80px rgba(110, 224, 106, 0.18)",
        panel: "0 20px 60px rgba(0, 0, 0, 0.18)"
      },
      backgroundImage: {
        ocean: "radial-gradient(circle at top, rgba(110,224,106,0.08), transparent 35%), linear-gradient(180deg, #0a1825 0%, #02080d 100%)"
      }
    }
  },
  plugins: []
};
