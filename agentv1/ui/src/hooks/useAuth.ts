import { useState, useEffect } from 'react';

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  isLoading: boolean;
  authStatus: string;
  isCheckingAuth: boolean;
}

interface AuthActions {
  handleOAuthLogin: () => Promise<void>;
}

export const useAuth = (): AuthState & AuthActions => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [authStatus, setAuthStatus] = useState<string>("Not authenticated");
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const checkExistingAuth = async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: "startOAuth",
        });

        if (response.success) {
          setToken(response.token);
          setIsAuthenticated(true);
          setAuthStatus("Already authenticated!");
        } else {
          setAuthStatus("Not authenticated");
        }
      } catch (error) {
        setAuthStatus("Not authenticated");
      } finally {
        setIsCheckingAuth(false);
      }
    };

    checkExistingAuth();
  }, []);

  const handleOAuthLogin = async () => {
    setIsLoading(true);
    setAuthStatus("Starting OAuth flow...");

    try {
      const response = await chrome.runtime.sendMessage({
        action: "startOAuth",
      });

      if (response.success) {
        setToken(response.token);
        setIsAuthenticated(true);
        setAuthStatus("Authenticated successfully!");
      } else {
        setAuthStatus(`Authentication failed: ${response.error}`);
      }
    } catch (error) {
      setAuthStatus(`Error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isAuthenticated,
    token,
    isLoading,
    authStatus,
    isCheckingAuth,
    handleOAuthLogin,
  };
};