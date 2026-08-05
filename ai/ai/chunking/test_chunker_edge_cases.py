import uuid
from semantic_chunker import SemanticChunker, ChunkConfig

def run_tests():
    config = ChunkConfig(min_tokens=20, max_tokens=100, overlap_tokens=10, similarity_threshold=0.6)
    chunker = SemanticChunker(config)
    metadata = {"title": "Test", "tribe_name": "TestTribe", "region": "TestRegion"}
    doc_id = "test_001"
    
    print("--- Test 1: Empty Input ---")
    chunks = chunker.chunk_document("", doc_id, metadata)
    print(f"Chunks created: {len(chunks)}")
    assert len(chunks) == 0

    print("\n--- Test 2: Very Small Document ---")
    small_text = "This is a small sentence. It is very short."
    chunks = chunker.chunk_document(small_text, doc_id, metadata)
    print(f"Chunks created: {len(chunks)}")
    assert len(chunks) == 1
    assert chunks[0]["token_count"] == chunker.count_tokens(small_text)
    
    print("\n--- Test 3: Document Exactly at Token Limit ---")
    # Build text precisely to max_tokens (100 tokens)
    text_100 = ""
    while chunker.count_tokens(text_100) < 100:
        text_100 += "word "
    text_100 = text_100.strip()
    chunks = chunker.chunk_document(text_100, doc_id, metadata)
    print(f"Chunks created: {len(chunks)}, Tokens: {chunks[0]['token_count']}")
    assert len(chunks) == 1
    assert chunks[0]["token_count"] <= 100
    
    print("\n--- Test 4: Document Above Token Limit ---")
    # Build text well over limit
    text_250 = ""
    for _ in range(300):
        text_250 += "sentence goes here. "
    chunks = chunker.chunk_document(text_250, doc_id, metadata)
    print(f"Chunks created: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i} tokens: {c['token_count']}")
        assert c["token_count"] <= 100
        
    print("\n--- Test 5: Multilingual Text ---")
    multi_text = "Here is some English. नमस्ते दुनिया. وهذا هو بعض العربية. Let's see how the tokenizer handles diverse scripts. Это русский текст."
    chunks = chunker.chunk_document(multi_text, doc_id, metadata)
    print(f"Chunks created: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i} tokens: {c['token_count']}")
        assert c["token_count"] <= 100

    print("\n--- Test 6: Noisy/OCR Text ---")
    noisy_text = "Warli art\n\n14\n\nIS A TRIBAL\nSTYLE\ncreated by people from North Sahyadri. It uses basic shapes."
    chunks = chunker.chunk_document(noisy_text, doc_id, metadata, source="ignca")
    print(f"Chunks created: {len(chunks)}")
    print(f"Cleaned Text: {chunks[0]['text']}")
    assert "14" not in chunks[0]['text']  # Should be cleaned out by ignca rule
    
    print("\nALL TESTS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    run_tests()
