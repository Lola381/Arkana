const API_BASE = "http://localhost:8000";

export async function analyzeImage(imageFile) {
  const formData = new FormData();
  formData.append("file", imageFile);

  const res = await fetch(`${API_BASE}/api/vision/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error(`Vision API error: ${res.status}`);
  return res.json();
}