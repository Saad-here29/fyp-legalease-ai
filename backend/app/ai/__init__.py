"""AI module — embeddings, FAISS index, RAG pipeline, LLM client, prompts.

The RAG pipeline implements Algorithm 5 from the Final Report:
    detect_language -> embed -> FAISS top-5 -> filter score >= 0.7
    -> compose_prompt -> LLM stream -> persist ChatMessage + citations.
"""
