"""
Benchmark Test Suite - BLDS 2015 Legal Document Retrieval
Chạy 5 benchmark queries và đánh giá kết quả
"""

from src import Document, EmbeddingStore, _mock_embed
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

def run_benchmark_test():
    """Chạy benchmark test trên 5 queries"""
    print("=" * 80)
    print("BENCHMARK TEST - BLDS 2015 Legal Document Retrieval")
    print("=" * 80)
    
    # Khởi tạo store
    store = EmbeddingStore(embedding_fn=_mock_embed)
    store.add_documents(LEGAL_DOCS)
    
    print(f"\n[OK] Loaded {store.get_collection_size()} documents\n")
    
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
        print(f"Question: {query}")
        print(f"\nGold Answer: {gold_answer[:100]}...")
        
        # Search with or without filter
        if metadata_filter:
            print(f"Filter: {metadata_filter}")
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
            content = result["content"][:60]
            doc_id = result.get("metadata", {}).get("source", "unknown")

            print(f"  {rank}. Score: {score:.3f} | {content}...")

            # Check if expected chunk is in top-3
            if expected_chunk in result["content"]:
                is_relevant = True
                if rank == 1:
                    top_1_score = score
                    total_score += score

        if is_relevant:
            relevant_count += 1
            status = "✅ RELEVANT (found in top-3)"
        else:
            status = "❌ NOT RELEVANT (not in top-3)"
        
        print(f"\nResult: {status}")
        
        results.append({
            "query_id": query_id,
            "query": query,
            "difficulty": difficulty,
            "relevant": is_relevant,
            "top_score": search_results[0]["score"] if search_results else 0,
            "has_filter": metadata_filter is not None
        })
    
    # Summary
    print(f"\n{'=' * 80}")
    print("BENCHMARK SUMMARY")
    print(f"{'=' * 80}")

    print(f"\nTotal Queries: {len(BENCHMARK_QUERIES)}")
    print(f"Relevant Results: {relevant_count}/{len(BENCHMARK_QUERIES)}")
    print(f"Success Rate: {relevant_count/len(BENCHMARK_QUERIES)*100:.1f}%")
    print(f"Average Score: {total_score/relevant_count:.3f}" if relevant_count > 0 else "N/A")

    # Detailed results table
    print(f"\n{'Query':<8} {'Difficulty':<12} {'Relevant':<12} {'Score':<10} {'Filter':<8}")
    print("-" * 60)
    for r in results:
        status = "[YES]" if r["relevant"] else "[NO]"
        filter_status = "[YES]" if r["has_filter"] else "[NO]"
        print(f"{r['query_id']:<8} {r['difficulty']:<12} {status:<12} {r['top_score']:<10.3f} {filter_status:<8}")

    # Breakdown by difficulty
    print(f"\n{'Difficulty Breakdown:':<30}")
    print("-" * 40)
    for difficulty in ["easy", "medium", "hard"]:
        count = sum(1 for r in results if r["difficulty"] == difficulty and r["relevant"])
        total = sum(1 for r in results if r["difficulty"] == difficulty)
        pct = count/total*100 if total > 0 else 0
        print(f"  {difficulty.upper():<10} {count}/{total} ({pct:.0f}%)")

    # Metadata filtering results
    print(f"\n{'Metadata Filtering:':<30}")
    print("-" * 40)
    with_filter = sum(1 for r in results if r["has_filter"] and r["relevant"])
    total_with_filter = sum(1 for r in results if r["has_filter"])
    without_filter = sum(1 for r in results if not r["has_filter"] and r["relevant"])
    total_without_filter = sum(1 for r in results if not r["has_filter"])

    print(f"  With Filter:    {with_filter}/{total_with_filter} ({with_filter/total_with_filter*100:.0f}%)")
    print(f"  Without Filter: {without_filter}/{total_without_filter} ({without_filter/total_without_filter*100:.0f}%)")

    print(f"\n{'=' * 80}")
    if relevant_count == len(BENCHMARK_QUERIES):
        print("[PASS] ALL TESTS PASSED!")
    else:
        print(f"[WARN] {len(BENCHMARK_QUERIES) - relevant_count} test(s) failed")
    print(f"{'=' * 80}\n")
    
    return results

if __name__ == "__main__":
    run_benchmark_test()
