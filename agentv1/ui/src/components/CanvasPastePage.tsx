import React, { useState } from "react";
import { TextField, Button, Box } from "@mui/material";
interface CanvasPastePageProps {
  onClassesLoaded: (
    classes: Array<{
      id: string;
      name: string;
      course_code: string;
    }>,
    canvasToken: string
  ) => void;
}
const CanvasPastePage: React.FC<CanvasPastePageProps> = ({
  onClassesLoaded,
}) => {
  const [canvasToken, setCanvasToken] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const handleSubmit = async () => {
    if (canvasToken.trim()) {
      setIsLoading(true);
      try {
        const response = await fetch("http://localhost:5001/api/courses", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            canvas_tokens: {
              access_token: canvasToken.trim(),
            },
          }),
        });
        if (response.ok) {
          const data = await response.json();
          console.log("Courses loaded:", data);
          // Transform the courses data to match our interface
          const classes = data.courses.map((course: any) => ({
            id: course.id?.toString() || "",
            name: course.name || "Unknown Course",
            course_code: course.course_code || "",
          }));
          onClassesLoaded(classes, canvasToken.trim());
          // Handle success - notify parent that classes are loaded
        } else {
          console.error("Failed to load courses");
        }
      } catch (error) {
        console.error("Error loading courses:", error);
      } finally {
        setIsLoading(false);
      }
    }
  };
  if (isLoading) {
    return (
      <Box sx={{ padding: "20px", width: "400px", textAlign: "center" }}>
        <h2>Loading Courses...</h2>
        <p>Fetching your Canvas courses, please wait...</p>
      </Box>
    );
  }
  return (
    <Box sx={{ padding: "20px", width: "400px" }}>
      <TextField
        label="Canvas API Token"
        variant="outlined"
        fullWidth
        multiline
        rows={3}
        placeholder="Paste your Canvas API token here..."
        value={canvasToken}
        onChange={(e) => setCanvasToken(e.target.value)}
        sx={{ marginBottom: "10px" }}
      />
      <Button
        variant="contained"
        onClick={handleSubmit}
        disabled={!canvasToken.trim()}
        sx={{ backgroundColor: "#1976D2", color: "white" }}
      >
        Submit
      </Button>
    </Box>
  );
};
export default CanvasPastePage;