console.log(" Background script is loading...");
function getGoogleToken() {
  return new Promise((resolve, reject) => {
    chrome.identity.getAuthToken({ interactive: true }, (result) => {
      if (chrome.runtime.lastError) {
        console.error("Chrome runtime error:", chrome.runtime.lastError);
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        console.log("Access token received:", result);
        resolve(result);
      }
    });
  });
}
async function sendQueryToAPI(query, token) {
  try {
    const response = await fetch("http://localhost:5000/query", {
      // Replace with your Flask endpoint
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query,
        google_token: token,
        // Pass the Google token as part of the query
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      })
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error("Flask API Error:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error occurred"
    };
  }
}
chrome.runtime.onMessage.addListener((request, _, sendResponse) => {
  console.log("Background script received message:", request);
  if (request.action === "startOAuth") {
    getGoogleToken().then((token) => {
      console.log("OAuth successful, token:", token);
      sendResponse({ success: true, token });
    }).catch((error) => {
      console.error("OAuth flow failed:", error);
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
  if (request.action === "sendQuery") {
    getGoogleToken().then(async (token) => {
      console.log("Sending query:", request.query);
      const result = await sendQueryToAPI(request.query, token);
      sendResponse(result);
    }).catch((error) => {
      console.error("Query failed:", error);
      sendResponse({
        success: false,
        error: error.message || "Failed to get token or send query"
      });
    });
    return true;
  }
  if (request.action === "ping") {
    sendResponse({ success: true, message: "Background script is alive" });
  }
});
chrome.runtime.onInstalled.addListener(() => {
  console.log("Chrome extension installed");
});
chrome.action.onClicked.addListener((tab) => {
  console.log("Extension icon clicked", tab);
});
console.log("Background script fully loaded!");
