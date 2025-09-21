import React from "react";

const Loading: React.FC = () => {
  return (
    <div
      style={{
        width: "400px",
        padding: "20px",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "200px",
      }}
    >
      <div>
        <h2>Loading...</h2>
        <p>Checking authentication status...</p>
      </div>
    </div>
  );
};

export default Loading;
