import { useAuth } from "./hooks";
import { Authentication, Home, Loading } from "./components";
import CanvasPastePage from "./components/CanvasPastePage";
import FinalRedirectScreen from "./components/FinalRedirectScreen";
import "./App.css";
import { useState } from "react";
import { ToastContainer } from "react-toastify";

import "react-toastify/dist/ReactToastify.css";
import { useEffect } from "react";
function App() {
  const {
    isAuthenticated,
    token,
    isLoading,
    authStatus,
    isCheckingAuth,
    handleOAuthLogin,
  } = useAuth();
  const [classesLoaded, setClassesLoaded] = useState(false);
  const [classes, setClasses] = useState<
    Array<{
      id: string;
      name: string;
      course_code: string;
    }>
  >([]);
  const [canvasToken, setCanvasToken] = useState<string | null>(null);
  const [showFinalRedirect, setShowFinalRedirect] = useState(false);
  const [redirectMessage, setRedirectMessage] = useState("");
  useEffect(() => {
    const canvasToken = localStorage.getItem("canvasToken");
    const classes = localStorage.getItem("classes");
    if (canvasToken && classes) {
      setCanvasToken(canvasToken);
      setClasses(JSON.parse(classes));
      setClassesLoaded(true);
    }
  }, []);
  // Show loading screen while checking authentication
  if (isCheckingAuth) {
    return <Loading />;
  }
  // Show authentication screen if not authenticated
  if (!isAuthenticated) {
    setClassesLoaded(false);
    return (
      <Authentication
        authStatus={authStatus}
        isLoading={isLoading}
        onLogin={handleOAuthLogin}
      />
    );
  }
  if (isAuthenticated && !classesLoaded) {
    return (
      <CanvasPastePage
        onClassesLoaded={(classesData, canvasToken) => {
          setClasses(classesData);
          setCanvasToken(canvasToken);
          localStorage.setItem("canvasToken", canvasToken);
          localStorage.setItem("classes", JSON.stringify(classesData));
          setClassesLoaded(true);
          console.log("Classes loaded:", classes);
        }}
      />
    );
    // canvas paste page now after submitting, hits the api with the api key from the CanvasPastePage
    // and then sets the classesLoaded state to true if the reponse is a success and classes are loaded
  }
  // Show final redirect screen after successful API call
  if (showFinalRedirect) {
    return (
      <FinalRedirectScreen
        onGoBack={() => setShowFinalRedirect(false)}
        message={redirectMessage}
      />
    );
  }
  //home should be passed the token and the classes array
  if (isAuthenticated && classesLoaded) {
    return (
      <>
        <Home
          token={token}
          classes={classes}
          canvasToken={canvasToken}
          onRedirectToFinal={(message) => {
            setRedirectMessage(message);
            setShowFinalRedirect(true);
          }}
        />
        <ToastContainer />
      </>
    );
  }
}
export default App;