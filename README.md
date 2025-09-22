For IEEE OC Computer Society AI Dev Hack 2025!

Andrew Bahsoun   
Sami Hammoud   
Landon Kauer   
Max Richter   


## Inspiration
We always thought extensions were an underexplored realm of development, and there are a lot of fun and powerful capabilities that can be hostedby such a lightweight tool
  
## What it does

The system uses secure Google Authentication to generate access tokens with Google Drive permissions. A Canvas scraper parses each course, extracting and organizing all associated files into a vector database. This database powers an agent equipped with tools for both advanced retrieval and dynamic content creation.

When prompted, the agent synthesizes insights from the processed course data, delivers precise and context-aware responses, and automatically documents results directly into Google Drive. The result is a fully automated knowledge pipeline that transforms raw academic content into structured, searchable intelligence while simultaneously generating polished written outputs for the user.

## How we built it
Uses React for frontend, ChromaDB for vector storage, Python for backend, and flask api to connect the frontend and backend. Uses Canvas API to scrape Canvas for relevant files, Drive API to write to Google Docs. Langchain and Gemini work together to provide the user with a meaningful experience.

## Challenges we ran into  
Not being communicative and clear on endpoints and JSON request/response structure. Created a lot of conflict and unnecessary frustration within the team :(!

## Accomplishments that we're proud of
Getting messages passed in from the user to pass through to the Gemini model and generate a response exclusively based on the files extracted under the specified canvas course

## What we learned
To create better detailed plans prior to development to make all parts more streamlined as they are created  

## What's next for CanvasAgent 
Full deployment and host on cloud, and potentially add Google Drive reading feature to add to canvas context

To run    
```
pip install -r requirements.txt
npm install
npm run build ( in /ui)
python index_txt_records.py
python app.py
```
You will need
- GOOGLE_API_KEY (free on https://aistudio.google.com/)
- OAuth 2.0 Client ID for a Chrome extension (https://developer.chrome.com/docs/extensions/how-to/integrate/oauth)
- CANVAS_ACCESS_TOKEN (can be made for free)





