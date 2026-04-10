#!/usr/bin/env python3
"""Demo script to showcase all implemented features."""

from src import (
    Document,
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
    ChunkingStrategyComparator,
    compute_similarity,
    EmbeddingStore,
    KnowledgeBaseAgent,
    _mock_embed,
)

# Sample text for demo
SAMPLE_TEXT = """
Python is a high-level programming language. It emphasizes code readability.
Python supports multiple programming paradigms. These include procedural, object-oriented, and functional programming.
Machine learning is a subset of artificial intelligence. It enables systems to learn from data.
Deep learning uses neural networks with many layers. It has revolutionized computer vision and NLP.
"""

def demo_chunking():
    """Demo all chunking strategies."""
    print("=" * 60)
    print("DEMO 1: Chunking Strategies")
    print("=" * 60)
    
    comparator = ChunkingStrategyComparator()
    result = comparator.compare(SAMPLE_TEXT, chunk_size=100)
    
    for strategy, stats in result.items():
        print(f"\n{strategy.upper()}:")
        print(f"  Chunks: {stats['count']}")
        print(f"  Avg length: {stats['avg_length']:.1f}")
        for i, chunk in enumerate(stats['chunks'][:2], 1):
            print(f"  Chunk {i}: {chunk[:60]}...")

def demo_similarity():
    """Demo cosine similarity."""
    print("\n" + "=" * 60)
    print("DEMO 2: Cosine Similarity")
    print("=" * 60)
    
    pairs = [
        ([1, 0, 0], [1, 0, 0]),  # identical
        ([1, 0, 0], [0, 1, 0]),  # orthogonal
        ([1, 0, 0], [-1, 0, 0]),  # opposite
        ([1, 1, 0], [1, 1, 0]),  # identical
    ]
    
    for a, b in pairs:
        sim = compute_similarity(a, b)
        print(f"  {a} vs {b}: {sim:.3f}")

def demo_embedding_store():
    """Demo EmbeddingStore."""
    print("\n" + "=" * 60)
    print("DEMO 3: EmbeddingStore")
    print("=" * 60)
    
    docs = [
        Document("doc1", "Python is a programming language", {"lang": "en"}),
        Document("doc2", "Machine learning uses algorithms", {"lang": "en"}),
        Document("doc3", "Deep learning with neural networks", {"lang": "en"}),
    ]
    
    store = EmbeddingStore(embedding_fn=_mock_embed)
    store.add_documents(docs)
    
    print(f"\nStored {store.get_collection_size()} documents")
    
    results = store.search("programming", top_k=2)
    print(f"\nSearch for 'programming':")
    for i, r in enumerate(results, 1):
        print(f"  {i}. Score: {r['score']:.3f}")
        print(f"     Content: {r['content'][:50]}...")

def demo_agent():
    """Demo KnowledgeBaseAgent."""
    print("\n" + "=" * 60)
    print("DEMO 4: KnowledgeBaseAgent (RAG)")
    print("=" * 60)
    
    docs = [
        Document("d1", "Python is a high-level language", {}),
        Document("d2", "Machine learning enables learning from data", {}),
    ]
    
    store = EmbeddingStore(embedding_fn=_mock_embed)
    store.add_documents(docs)
    
    def mock_llm(prompt):
        return "Answer: Python is a versatile programming language."
    
    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)
    answer = agent.answer("What is Python?", top_k=2)
    print(f"\nAgent answer:\n{answer}")

if __name__ == "__main__":
    demo_chunking()
    demo_similarity()
    demo_embedding_store()
    demo_agent()
    print("\n" + "=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)
