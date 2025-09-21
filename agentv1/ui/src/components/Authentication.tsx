import React from "react";
import GoogleSignInButton from "./GoogleSignInButton";

interface AuthenticationProps {
  authStatus: string;
  isLoading: boolean;
  onLogin: () => void;
}

const Authentication: React.FC<AuthenticationProps> = ({
  authStatus,
  isLoading,
  onLogin,
}) => {
  return (
    <div style={{ width: "400px", padding: "20px" }}>
      <h1>Chrome Extension OAuth2 Demo</h1>
      <div className="card">
        <h2>Authentication</h2>
        <p>Status: {authStatus}</p>
        <GoogleSignInButton
          onClick={onLogin}
          isLoading={isLoading}
          size="medium"
          color="light"
        />
      </div>
    </div>
  );
};

export default Authentication;
