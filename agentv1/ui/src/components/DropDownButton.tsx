// import React, { useState } from "react";
import {
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent,
} from "@mui/material";

interface DropDownButtonProps {
  title?: string;
  value: string;
  onChange: (value: string) => void;
  items: Array<{
    label: string;
    value: string;
  }>;
  size?: "small" | "medium";
}

const DropDownButton: React.FC<DropDownButtonProps> = ({
  title = "Class Options",
  value,
  onChange,
  items,
  size = "small",
}) => {
  const handleChange = (event: SelectChangeEvent<string>) => {
    const selectedValue = event.target.value;
    onChange(selectedValue);
  };

  return (
    <FormControl size={size} sx={{ minWidth: 120 }}>
      <InputLabel id="dropdown-select-label">{title}</InputLabel>
      <Select
        labelId="dropdown-select-label"
        id="dropdown-select"
        value={value}
        label={title}
        onChange={handleChange}
      >
        {items.map((item, index) => (
          <MenuItem key={index} value={item.value}>
            {item.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default DropDownButton;
