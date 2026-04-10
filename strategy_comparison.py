"""
Strategy Comparison - Phase 2
3 different chunking strategies tested on same benchmark queries
"""

from src import Document, EmbeddingStore, _mock_embed
from src.chunking import SentenceChunker, RecursiveChunker, FixedSizeChunker
from benchmark_queries import BENCHMARK_QUERIES

# Legal documents for testing
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

class StrategyComparison:
    """Compare different chunking strategies"""
    
    def __init__(self):
        self.strategies = {
            "sentence": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=300),
            "fixed": FixedSizeChunker(chunk_size=200, overlap=50),
        }
    
    def run_comparison(self):
        """Run all strategies on benchmark queries"""
        results = {}
        
        for strategy_name, chunker in self.strategies.items():
            print(f"\n{'='*70}")
            print(f"STRATEGY: {strategy_name.upper()}")
            print(f"{'='*70}")
            
            store = EmbeddingStore(embedding_fn=_mock_embed)
            store.add_documents(LEGAL_DOCS)
            
            strategy_results = []
            total_score = 0
            
            for query_data in BENCHMARK_QUERIES:
                query = query_data["query"]
                query_id = query_data["id"]
                
                # Search with optional metadata filter
                if query_data["metadata_filter"]:
                    results_list = store.search_with_filter(
                        query, 
                        top_k=2,
                        metadata_filter=query_data["metadata_filter"]
                    )
                else:
                    results_list = store.search(query, top_k=2)
                
                score = results_list[0]["score"] if results_list else 0
                total_score += score
                
                strategy_results.append({
                    "query_id": query_id,
                    "score": score,
                    "retrieved": results_list[0]["content"][:50] if results_list else "N/A"
                })
                
                print(f"\nQuery {query_id}: {query[:50]}...")
                print(f"  Score: {score:.3f}")
                if results_list:
                    print(f"  Retrieved: {results_list[0]['content'][:60]}...")
            
            avg_score = total_score / len(BENCHMARK_QUERIES)
            results[strategy_name] = {
                "avg_score": avg_score,
                "queries": strategy_results
            }
            
            print(f"\n{strategy_name.upper()} Average Score: {avg_score:.3f}")
        
        return results

if __name__ == "__main__":
    comparison = StrategyComparison()
    results = comparison.run_comparison()
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for strategy, data in results.items():
        print(f"{strategy.upper()}: {data['avg_score']:.3f}")
