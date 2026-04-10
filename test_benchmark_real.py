"""
Benchmark Test with Real Embeddings (Sentence-Transformers)
Chạy 5 benchmark queries với real embeddings
"""

import os
from src import Document, EmbeddingStore
from src.embeddings import LocalEmbedder
from benchmark_queries import BENCHMARK_QUERIES

# Legal documents
LEGAL_DOCS = [
    Document(
        "article_292",
        "Điều 292 BLDS 2015 quy định các biện pháp bảo đảm thực hiện nghĩa vụ bao gồm: cầm cố tài sản; thế chấp tài sản; đặt cọc; ký cược; ký quỹ; bảo lưu quyền sở hữu; bảo lãnh; tín chấp và cầm giữ tài sản.",
        {"type": "article", "number": 292, "year": 2015, "category": "guarantee"}
    ),
    Document(
        "article_293",
        "Điều 293 BLDS 2015 quy định về phạm vi nghĩa vụ được bảo đảm. Khoản 1: Nghĩa vụ có thể được bảo đảm một phần hoặc toàn bộ. Nếu không có thỏa thuận, nghĩa vụ được bảo đảm toàn bộ, kể cả lãi, tiền phạt và bồi thương.",
        {"type": "article", "number": 293, "year": 2015, "category": "guarantee"}
    ),
    Document(
        "article_295",
        "Điều 295 BLDS 2015 quy định tài sản bảo đảm phải thuộc quyền sở hữu bên bảo đảm, xác định được, có thể là tài sản hiện có hoặc tương lai, giá trị có thể lớn hơn/bằng/nhỏ hơn nghĩa vụ.",
        {"type": "article", "number": 295, "year": 2015, "category": "asset"}
    ),
    Document(
        "article_297",
        "Điều 297 BLDS 2015 quy định hiệu lực đối kháng với người thứ ba. Biện pháp bảo đảm phát sinh hiệu lực từ khi đăng ký hoặc bên nhận bảo đảm nắm giữ/chiếm giữ tài sản. Bên nhận bảo đảm có quyền truy đòi tài sản và ưu tiên thanh toán.",
        {"type": "article", "number": 297, "year": 2015, "category": "guarantee"}
    ),
    Document(
        "article_308",
        "Điều 308 BLDS 2015 quy định thứ tự ưu tiên thanh toán. Nếu các biện pháp đều có hiệu lực đối kháng, ưu tiên theo thứ tự xác lập. Nếu có/không có hiệu lực, biện pháp có hiệu lực được ưu tiên. Nếu đều không có, ưu tiên theo thứ tự xác lập.",
        {"type": "article", "number": 308, "year": 2015, "category": "procedure"}
    ),
]

def run_benchmark_with_real_embeddings():
    """Chạy benchmark test với real embeddings"""
    print("=" * 80)
    print("BENCHMARK TEST - Real Embeddings (Sentence-Transformers)")
    print("=" * 80)
    
    try:
        # Khởi tạo LocalEmbedder
        embedder = LocalEmbedder(model_name="sentence-transformers/all-MiniLM-L6-v2")
        print(f"\n✓ Using: {embedder._backend_name}\n")
    except Exception as e:
        print(f"\n⚠️  Could not load real embeddings: {e}")
        print("Falling back to mock embeddings\n")
        from src import _mock_embed
        embedder = _mock_embed
    
    # Khởi tạo store
    store = EmbeddingStore(embedding_fn=embedder)
    store.add_documents(LEGAL_DOCS)
    
    print(f"✓ Loaded {store.get_collection_size()} documents\n")
    
    results = []
    total_score = 0
    relevant_count = 0
    
    for query_data in BENCHMARK_QUERIES:
        query_id = query_data["id"]
        query = query_data["query"]
        gold_answer = query_data["gold_answer"]
        expected_chunk = query_data["expected_chunk"]
        metadata_filter = query_data["metadata_filter"]
        difficulty = query_data["difficulty"]
        
        print(f"\n{'─' * 80}")
        print(f"Query {query_id} ({difficulty.upper()}) - {expected_chunk}")
        print(f"{'─' * 80}")
        print(f"Q: {query[:70]}...")
        
        # Search with or without filter
        if metadata_filter:
            search_results = store.search_with_filter(
                query, 
                top_k=3,
                metadata_filter=metadata_filter
            )
        else:
            search_results = store.search(query, top_k=3)
        
        # Evaluate results
        print(f"\nTop-3 Results:")
        is_relevant = False
        top_1_score = 0
        
        for rank, result in enumerate(search_results, 1):
            score = result["score"]
            content = result["content"][:50]
            
            print(f"  {rank}. {score:.3f} | {content}...")
            
            # Check if expected chunk is in top-3
            if expected_chunk in result["content"]:
                is_relevant = True
                if rank == 1:
                    top_1_score = score
                    total_score += score
        
        if is_relevant:
            relevant_count += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"Result: {status}")
        
        results.append({
            "query_id": query_id,
            "relevant": is_relevant,
            "top_score": search_results[0]["score"] if search_results else 0,
            "difficulty": difficulty,
            "has_filter": metadata_filter is not None
        })
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    
    success_rate = relevant_count/len(BENCHMARK_QUERIES)*100
    print(f"\nRelevant: {relevant_count}/{len(BENCHMARK_QUERIES)} ({success_rate:.0f}%)")
    
    print(f"\n{'Query':<8} {'Difficulty':<12} {'Result':<12} {'Score':<10}")
    print("─" * 50)
    for r in results:
        status = "✅ PASS" if r["relevant"] else "❌ FAIL"
        print(f"{r['query_id']:<8} {r['difficulty']:<12} {status:<12} {r['top_score']:<10.3f}")
    
    print(f"\n{'=' * 80}")
    if relevant_count == len(BENCHMARK_QUERIES):
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"⚠️  {len(BENCHMARK_QUERIES) - relevant_count} test(s) failed")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    run_benchmark_with_real_embeddings()
