import React, { useState } from "react";
import SearchInput from "./SearchInput";
import DropDownButton from "./DropDownButton";
import Button from "@mui/material/Button";
import { motion } from "framer-motion";
import { textAnimations } from "../styles/textStyles";
import { toast } from "react-toastify";
interface HomeProps {
  token: string | null;
  classes: Array<{
    id: string;
    name: string;
    course_code: string;
  }>;
  canvasToken: string | null;
  onRedirectToFinal: (message: string) => void;
}
const Home: React.FC<HomeProps> = ({
  token,
  classes,
  canvasToken,
  onRedirectToFinal,
}) => {
  const [searchText, setSearchText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedClass, setSelectedClass] = useState("");
  const handleSubmit = async () => {
    if (selectedClass === "") {
      toast.error("Please select as class!");
      return;
    }
    if (!searchText.trim() || !token) return;
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:5001/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: searchText,
          context: {
            courses: [selectedClass], // <-- matches your desired format
          },
          canvas_tokens: {
            access_token: canvasToken,
          },
          google_tokens: {
            access_token: token,
          },
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(selectedClass);
      console.log("API Response:", data);
      // Redirect to final screen after successful API response
      //neds to send data.message to the final redirect screen
      onRedirectToFinal(data.message);
    } catch (error) {
      console.error("API Error:", error);
    } finally {
      setIsLoading(false);
    }
    setSearchText("");
  };
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };
  return (
    <div style={{ width: "400px", padding: "20px" }}>
      <motion.h1 {...textAnimations.elegant}>Personal-Wizard</motion.h1>
      <div>
        <SearchInput
          val={searchText}
          onChange={setSearchText}
          onKeyPress={handleKeyPress}
          isLoading={isLoading}
        />
        {/* Horizontal layout for submit button and dropdown */}
        <div
          style={{
            display: "flex",
            gap: "10px",
            alignItems: "flex-start",
            marginTop: "10px",
          }}
        >
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!searchText.trim() || isLoading}
            style={{
              backgroundColor: "#1976D2",
              color: "white",
              flex: "0 0 auto",
            }}
          >
            {isLoading ? "Sending..." : "Send To Wizard"}
          </Button>
          {/*Needs to dynamically render based on classes pulled from API call*/}
          <DropDownButton
            title="Class Options"
            value={selectedClass}
            onChange={setSelectedClass}
            items={classes.map((course) => ({
              label: course.name,
              value: course.name,
            }))}
          />
        </div>
      </div>
    </div>
  );
};
export default Home;