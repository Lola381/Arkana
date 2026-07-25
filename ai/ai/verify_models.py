import os
from dotenv import load_dotenv
load_dotenv()

print("=== Arkana Model Verification ===\n")

print("1. Loading embedding model (sentence-transformers/all-mpnet-base-v2)...")
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer("all-mpnet-base-v2")
test_embed = embedder.encode(["Warli tribal painting from Maharashtra"])
assert test_embed.shape == (1, 768), f"Expected (1, 768), got {test_embed.shape}"
print(f"   ✓ Embedding shape: {test_embed.shape}\n")

print("2. Loading cross-encoder reranker (ms-marco-MiniLM-L-6-v2)...")
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
test_score = reranker.predict([("what is Warli art", "Warli is a tribal art form from Maharashtra")])
print(f"   ✓ Reranker score: {test_score[0]:.4f}\n")

print("3. Loading CLIP (ViT-B/32)...")
import clip, torch
model, preprocess = clip.load("ViT-B/32", device="cpu")
print(f"   ✓ CLIP loaded on cpu\n")

print("4. Loading spaCy NER (en_core_web_sm)...")
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp("Warli painting originates from Maharashtra near Mumbai.")
ents = [(e.text, e.label_) for e in doc.ents]
print(f"   ✓ Entities found: {ents}\n")

print("5. Testing Groq connection...")
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Reply with exactly: ARKANA_OK"}],
    max_tokens=20
)
reply = response.choices[0].message.content.strip()
print(f"   ✓ Groq response: {reply}\n")

print("=== All checks passed. Ready for Week 2. ===")