// Import Google Fonts
import "@fontsource/inter/400.css";
import "@fontsource/inter/700.css";
import "@fontsource/inter/900.css";
import "@fontsource/playfair-display/400.css";
import "@fontsource/playfair-display/700.css";
import "@fontsource/merriweather/400.css";
import "@fontsource/merriweather/700.css";
import "@fontsource/roboto-mono/400.css";
import "@fontsource/roboto-mono/500.css";
import "@fontsource/roboto-mono/700.css";
import "@fontsource/bungee/400.css";

export const textAnimations = {
  // Elegant serif font with golden styling
 

  // Bold display font with fun styling
  elegant: {
    initial: { opacity: 0, scale: 0.8 },
    animate: { 
      opacity: 1, 
      scale: [1, 1.05, 1],
      y: [0, -8, 0]
    },
    transition: { 
      opacity: { duration: 0.6, ease: "easeOut" as const },
      scale: { 
        duration: 2, 
        repeat: Infinity, 
        ease: "easeInOut" as const 
      },
      y: { 
        duration: 2, 
        repeat: Infinity, 
        ease: "easeInOut" as const 
      }
    },
    style: {
      fontFamily: "Bungee, cursive",
      color: "#ff6b35",
      fontWeight: "400",
      letterSpacing: "2px",
      fontSize: "2.5rem",
      textTransform: "uppercase" as const,
      textShadow: "3px 3px 0px #333, 6px 6px 0px rgba(0,0,0,0.3)",
      lineHeight: "1.1",
    }
  },

  // Modern bold with tech styling
  modern: {
    initial: { opacity: 0, rotateX: -90 },
    animate: { opacity: 1, rotateX: 0 },
    transition: { duration: 0.8, ease: "easeOut" as const },
    style: {
      fontFamily: "Inter, sans-serif",
      color: "#1f2937",
      fontWeight: "900",
      letterSpacing: "1px",
      fontSize: "2.2rem",
      textTransform: "uppercase" as const,
    }
  },

  // Monospace coding style
  monospace: {
    style: {
      fontFamily: "Roboto Mono, monospace",
      color: "#666",
      fontSize: "14px",
      lineHeight: "1.4",
      fontWeight: "400",
    }
  }
};
