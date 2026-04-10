"""
Custom chunking strategy for Vietnamese legal documents (Bộ Luật Dân Sự 2015)

Domain: Legal documents with hierarchical structure
- Sections (Chương, Mục)
- Articles (Điều)
- Clauses (Khoản)
- Examples (Ví dụ)

Strategy: Chunk by legal structure to preserve context
"""

from src import Document, EmbeddingStore, _mock_embed


class LegalDocumentChunker:
    """
    Custom chunker for Vietnamese legal documents.
    
    Preserves legal structure:
    - Sections (Chương, Mục)
    - Articles (Điều)
    - Clauses (Khoản)
    
    Design rationale:
    Legal documents have hierarchical structure. Chunking by article/clause
    preserves legal context and makes retrieval more accurate for legal queries.
    """
    
    def __init__(self, max_chunk_size: int = 800):
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, text: str) -> list[str]:
        """Chunk legal document by articles and clauses."""
        if not text:
            return []
        
        chunks = []
        current_chunk = ""
        
        # Split by article markers (Điều)
        lines = text.split('\n')
        
        for line in lines:
            # Check if line is an article header
            if line.strip().startswith('Điều') or line.strip().startswith('CHƯƠNG'):
                # Save previous chunk if exists
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                # Add line to current chunk
                if len(current_chunk) + len(line) < self.max_chunk_size:
                    current_chunk += '\n' + line
                else:
                    # Save current chunk and start new one
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = line
        
        # Add last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if c.strip()]


def demo_legal_strategy():
    """Demo the legal document chunking strategy."""
    print("=" * 70)
    print("DEMO: Legal Document Chunking Strategy")
    print("=" * 70)
    
    # Sample legal text
    sample_legal = """
Điều 292 BLDS 2015 quy định các biện pháp bảo đảm thực hiện nghĩa vụ bao gồm: 
cầm cố tài sản; thế chấp tài sản; đặt cọc; ký cược; ký quỹ; bảo lưu quyền sở hữu; 
bảo lãnh; tín chấp và cầm giữ tài sản.

Khoản 1: Bên bảo đảm phải thuộc quyền sở hữu của bên bảo đảm, trừ trường hợp 
cầm giữ tài sản, bảo lưu quyền sở hữu.

Khoản 2: Tài sản bảo đảm có thể được mô tả chung, nhưng phải xác định được.

Điều 293 BLDS 2015 quy định về phạm vi nghĩa vụ được bảo đảm:
Khoản 1: Nghĩa vụ có thể được bảo đảm một phần hoặc toàn bộ theo thỏa thuận 
hoặc theo quy định của pháp luật.

Khoản 2: Trường hợp bảo đảm nghĩa vụ trong tương lai thì nghĩa vụ được hình thành 
trong thời hạn bảo đảm là nghĩa vụ được bảo đảm.
"""
    
    # Test chunking
    chunker = LegalDocumentChunker(max_chunk_size=500)
    chunks = chunker.chunk(sample_legal)
    
    print(f"\nChunked into {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  Length: {len(chunk)} chars")
        print(f"  Preview: {chunk[:80]}...")
        print()


def demo_legal_retrieval():
    """Demo retrieval on legal documents."""
    print("=" * 70)
    print("DEMO: Legal Document Retrieval")
    print("=" * 70)
    
    # Create store with legal documents
    store = EmbeddingStore(embedding_fn=_mock_embed)
    
    legal_docs = [
        Document(
            "article_292",
            "Điều 292 BLDS 2015 quy định các biện pháp bảo đảm thực hiện nghĩa vụ",
            {"type": "article", "number": 292, "year": 2015, "category": "guarantee"}
        ),
        Document(
            "article_293",
            "Điều 293 BLDS 2015 quy định về phạm vi nghĩa vụ được bảo đảm",
            {"type": "article", "number": 293, "year": 2015, "category": "guarantee"}
        ),
        Document(
            "article_295",
            "Điều 295 BLDS 2015 quy định về tài sản bảo đảm thực hiện nghĩa vụ",
            {"type": "article", "number": 295, "year": 2015, "category": "asset"}
        ),
    ]
    
    store.add_documents(legal_docs)
    
    # Test queries
    queries = [
        "Các biện pháp bảo đảm thực hiện nghĩa vụ là gì?",
        "Tài sản bảo đảm phải có điều kiện gì?",
        "Phạm vi nghĩa vụ được bảo đảm bao gồm những gì?",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = store.search(query, top_k=2)
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f}")
            print(f"     Content: {result['content'][:60]}...")


if __name__ == "__main__":
    demo_legal_strategy()
    demo_legal_retrieval()
    print("\n" + "=" * 70)
    print("Legal document strategy demo completed!")
    print("=" * 70)
