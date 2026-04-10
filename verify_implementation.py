#!/usr/bin/env python3
"""
Verification script - Kiểm tra tất cả implementations
"""

def verify_all():
    print("=" * 70)
    print("VERIFICATION: LAB 7 - EMBEDDING & VECTOR STORE")
    print("=" * 70)
    
    # Test imports
    print("\n1. Testing imports...")
    try:
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
        print("   ✅ All imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test SentenceChunker
    print("\n2. Testing SentenceChunker...")
    try:
        chunker = SentenceChunker(max_sentences_per_chunk=2)
        text = "Hello world. This is a test. Another sentence here."
        chunks = chunker.chunk(text)
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)
        print(f"   ✅ SentenceChunker works ({len(chunks)} chunks)")
    except Exception as e:
        print(f"   ❌ SentenceChunker failed: {e}")
        return False
    
    # Test RecursiveChunker
    print("\n3. Testing RecursiveChunker...")
    try:
        chunker = RecursiveChunker(chunk_size=100)
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        chunks = chunker.chunk(text)
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)
        print(f"   ✅ RecursiveChunker works ({len(chunks)} chunks)")
    except Exception as e:
        print(f"   ❌ RecursiveChunker failed: {e}")
        return False
    
    # Test compute_similarity
    print("\n4. Testing compute_similarity...")
    try:
        sim1 = compute_similarity([1, 0, 0], [1, 0, 0])
        sim2 = compute_similarity([1, 0, 0], [0, 1, 0])
        assert abs(sim1 - 1.0) < 0.001
        assert abs(sim2 - 0.0) < 0.001
        print(f"   ✅ compute_similarity works (identical: {sim1:.3f}, orthogonal: {sim2:.3f})")
    except Exception as e:
        print(f"   ❌ compute_similarity failed: {e}")
        return False
    
    # Test ChunkingStrategyComparator
    print("\n5. Testing ChunkingStrategyComparator...")
    try:
        comparator = ChunkingStrategyComparator()
        result = comparator.compare("Test text " * 50, chunk_size=100)
        assert "fixed_size" in result
        assert "by_sentences" in result
        assert "recursive" in result
        print(f"   ✅ ChunkingStrategyComparator works (3 strategies)")
    except Exception as e:
        print(f"   ❌ ChunkingStrategyComparator failed: {e}")
        return False
    
    # Test EmbeddingStore
    print("\n6. Testing EmbeddingStore...")
    try:
        store = EmbeddingStore(embedding_fn=_mock_embed)
        docs = [
            Document("d1", "Python is a language", {}),
            Document("d2", "Machine learning is AI", {}),
        ]
        store.add_documents(docs)
        assert store.get_collection_size() == 2
        results = store.search("Python", top_k=1)
        assert len(results) > 0
        assert "content" in results[0]
        assert "score" in results[0]
        print(f"   ✅ EmbeddingStore works (stored: {store.get_collection_size()}, search: {len(results)} results)")
    except Exception as e:
        print(f"   ❌ EmbeddingStore failed: {e}")
        return False
    
    # Test search_with_filter
    print("\n7. Testing search_with_filter...")
    try:
        store = EmbeddingStore(embedding_fn=_mock_embed)
        docs = [
            Document("d1", "Python", {"lang": "en"}),
            Document("d2", "Java", {"lang": "en"}),
            Document("d3", "Python", {"lang": "vi"}),
        ]
        store.add_documents(docs)
        results = store.search_with_filter("Python", top_k=5, metadata_filter={"lang": "en"})
        assert all(r["metadata"]["lang"] == "en" for r in results)
        print(f"   ✅ search_with_filter works (filtered: {len(results)} results)")
    except Exception as e:
        print(f"   ❌ search_with_filter failed: {e}")
        return False
    
    # Test delete_document
    print("\n8. Testing delete_document...")
    try:
        store = EmbeddingStore(embedding_fn=_mock_embed)
        docs = [Document("d1", "Content", {})]
        store.add_documents(docs)
        size_before = store.get_collection_size()
        deleted = store.delete_document("d1")
        size_after = store.get_collection_size()
        assert deleted == True
        assert size_after < size_before
        print(f"   ✅ delete_document works (before: {size_before}, after: {size_after})")
    except Exception as e:
        print(f"   ❌ delete_document failed: {e}")
        return False
    
    # Test KnowledgeBaseAgent
    print("\n9. Testing KnowledgeBaseAgent...")
    try:
        store = EmbeddingStore(embedding_fn=_mock_embed)
        docs = [Document("d1", "Python is great", {})]
        store.add_documents(docs)
        agent = KnowledgeBaseAgent(store=store, llm_fn=lambda p: "Test answer")
        answer = agent.answer("What is Python?")
        assert isinstance(answer, str)
        assert len(answer) > 0
        print(f"   ✅ KnowledgeBaseAgent works (answer: {answer[:40]}...)")
    except Exception as e:
        print(f"   ❌ KnowledgeBaseAgent failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL VERIFICATIONS PASSED!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    import sys
    success = verify_all()
    sys.exit(0 if success else 1)
