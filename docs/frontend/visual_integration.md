# Arkana Visual Pipeline — Frontend Integration Guide

This document outlines the implementation strategy for the Visual Identity feature in the React frontend. 

## The Objective
When a user uploads a photo of an Indian monument or art piece, the frontend should instantly display both the **identified style** and the **full historical background** of that style on the same page.

## The Architecture: "Option A"
To keep the application highly responsive and modular, we are utilizing **Frontend Orchestration (Option A)**. 
This means the frontend will chain two API calls together behind the scenes, rather than forcing the backend to do everything in one blocking request.

### Step-by-Step Implementation

#### 1. The Identification Call
When the user selects an image, immediately show a loading spinner (e.g., "Analyzing Image...").
Make a `multipart/form-data` POST request to `/api/identify`.

```javascript
// Example Request
const formData = new FormData();
formData.append('image', imageFile);

const response = await fetch('http://localhost:8000/api/identify', {
    method: 'POST',
    body: formData
});
const data = await response.json();

// Example Response data:
// {
//   "style_classification": { "top_style": "Dravidian temple architecture", "confidence": 0.95, ... },
//   "rag_query": "What is the cultural significance and historical context of Dravidian temple architecture?",
//   "similar_artifacts": [],
//   "rag_context": {}
// }
```

**UI Action:** Update the screen to display the identified style (e.g., "Identified: Dravidian Temple Architecture"). Do NOT stop the loading spinner yet. Change the spinner text to "Searching historical records...".

#### 2. The Chat/RAG Call
Take the `rag_query` string returned from Step 1 and immediately send it to the `/api/chat` endpoint. This is the exact same endpoint the standard chat box uses.

```javascript
// Example Request
const chatResponse = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: data.rag_query,
        history: [], // Optional
        map_context: {} // Optional
    })
});
```

**UI Action:** The `/api/chat` endpoint streams Server-Sent Events (SSE). Render this stream directly below the identified image, exactly as you would in the chat interface.

### Summary of Benefits
By chaining `/api/identify` -> `/api/chat` on the frontend:
1. The user gets immediate visual feedback that the AI recognized their image.
2. The UI doesn't freeze while the backend searches the database.
3. The historical text streams beautifully onto the screen.

---

### Step 3: The "Want to know more?" Transition (UX Recommendation)
Since the user is currently on the "Identify Image" page, they might want to ask follow-up questions about the historical text that was just generated.

**Recommendation:** 
After the `/api/chat` stream finishes loading on the image page, display a button below the text: 
`[ Want to know more? Chat with Arkana ]`

When clicked, the frontend should:
1. Navigate the user to the main Chat UI page.
2. Pass the generated text as the initial "Conversation History" so the Chat UI knows exactly what the user is talking about, allowing them to ask seamless follow-up questions like *"Where is this temple located?"* without losing context.
