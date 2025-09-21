import React, { useState } from "react";
import TextField from "@mui/material/TextField";
import LoopingPlaceholder from "./LoopingPlaceholder";

interface SearchInputProps {
  val: string;
  onChange: (value: string) => void;
  onKeyPress?: (e: React.KeyboardEvent) => void;
  isLoading?: boolean;
  placeholder?: string;
}

const SearchInput: React.FC<SearchInputProps> = ({
  val,
  onChange,
  onKeyPress,
  isLoading = false,
}) => {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div
      style={{
        width: "100%",
        position: "relative",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <TextField
        id="search-input"
        multiline
        rows={4}
        placeholder=""
        value={val}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyPress}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        style={{ width: "100%" }}
        variant="outlined"
        disabled={isLoading}
      />

      {/* Animated placeholder overlay - shows when no input and not focused */}
      {!val && !isFocused && (
        <div
          style={{
            position: "absolute",
            top: "16px",
            left: "16px",
            pointerEvents: "auto",
            color: "#666",
            fontSize: "16px",
            lineHeight: "1.5",
            zIndex: 1,
            cursor: "text",
            whiteSpace: "nowrap",
            overflow: "hidden",
          }}
          onClick={() => {
            // Focus the TextField when overlay is clicked
            setIsFocused(true);
            const textField = document.getElementById("search-input");
            if (textField) {
              textField.focus();
            }
          }}
        >
          <LoopingPlaceholder />
        </div>
      )}
    </div>
  );
};

export default SearchInput;
