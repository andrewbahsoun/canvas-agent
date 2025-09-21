import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { textAnimations } from "../styles/textStyles";
import { IconButton } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

interface FinalRedirectScreenProps {
  onGoBack: () => void;
  message: string;
}

const FinalRedirectScreen: React.FC<FinalRedirectScreenProps> = ({
  onGoBack,
  message,
}) => {
  const [displayText, setDisplayText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < message.length) {
      const timeout = setTimeout(() => {
        setDisplayText(message.substring(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, 5); // Typing speed - 20ms per character

      return () => clearTimeout(timeout);
    }
  }, [currentIndex, message]);
  return (
    <div style={{ width: "400px", padding: "20px", position: "relative" }}>
      <IconButton
        onClick={onGoBack}
        sx={{
          position: "absolute",
          top: "10px",
          left: "10px",
          zIndex: 1,
        }}
      >
        <ArrowBackIcon />
      </IconButton>

      <motion.h1 {...textAnimations.elegant}>Personal-Wizard</motion.h1>
      <div>
        <p style={textAnimations.monospace.style}>{displayText}</p>
      </div>
    </div>
  );
};

export default FinalRedirectScreen;
