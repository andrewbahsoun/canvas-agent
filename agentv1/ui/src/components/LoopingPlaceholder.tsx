import { useEffect, useState } from "react";
import { textAnimations } from "../styles/textStyles";

export default function LoopingPlaceholder() {
  const texts: string[] = [
    "What did my teacher say LangChain did?",
    "Generate study notes for CS203...",
    "Generate study notes for Philosophy 310",
    "Create a template for my next lecture...",
    "Create a study guide for Chapter 5...",
    "Create a study guide for Chapter 2...",
  ];

  const [displayText, setDisplayText] = useState<string>("");
  const [index, setIndex] = useState<number>(0);
  const [subIndex, setSubIndex] = useState<number>(0);
  const [deleting, setDeleting] = useState<boolean>(false);
  const [hasStarted, setHasStarted] = useState<boolean>(false);

  useEffect(() => {
    // Initial delay before starting to type
    if (!hasStarted) {
      const initialTimeout = setTimeout(() => {
        setHasStarted(true);
      }, 1500); // 1.5 second delay
      return () => clearTimeout(initialTimeout);
    }

    const current = texts[index];
    const nextIndex = (index + 1) % texts.length;
    const nextText = texts[nextIndex];

    // Find common prefix between current and next text
    const findCommonPrefix = (text1: string, text2: string) => {
      let commonLength = 0;
      const minLength = Math.min(text1.length, text2.length);
      for (let i = 0; i < minLength; i++) {
        if (text1[i] === text2[i]) {
          commonLength++;
        } else {
          break;
        }
      }
      return commonLength;
    };

    const commonPrefixLength = findCommonPrefix(current, nextText);
    let timeout: ReturnType<typeof setTimeout>;

    if (!deleting && subIndex < current.length) {
      // Typing out current text
      timeout = setTimeout(() => setSubIndex(subIndex + 1), 100);
    } else if (deleting && subIndex > commonPrefixLength) {
      // Deleting back to common prefix
      timeout = setTimeout(() => setSubIndex(subIndex - 1), 50);
    } else if (!deleting && subIndex === current.length) {
      // Finished typing, start deleting after pause
      timeout = setTimeout(() => setDeleting(true), 1000);
    } else if (deleting && subIndex === commonPrefixLength) {
      // Finished deleting to common prefix, move to next text
      setDeleting(false);
      setIndex(nextIndex);
    }

    setDisplayText(current.substring(0, subIndex));
    return () => clearTimeout(timeout);
  }, [subIndex, deleting, index, texts, hasStarted]);

  return <span style={textAnimations.monospace.style}>{displayText}</span>;
}
