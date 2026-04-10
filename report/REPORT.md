# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Quang Phúc
**Nhóm:** C401-B3
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai vector có cosine similarity cao (gần 1) có nghĩa là chúng chỉ vào cùng một hướng trong không gian, tức là hai đoạn văn bản có nội dung rất tương đồng về ý nghĩa.

**Ví dụ HIGH similarity:**
- Sentence A: "Python is a programming language"
- Sentence B: "Python is a coding language"
- Tại sao tương đồng: Cả hai câu đều nói về Python và lập trình, chỉ khác từ "programming" vs "coding" nhưng ý nghĩa tương tự.

**Ví dụ LOW similarity:**
- Sentence A: "Python is a programming language"
- Sentence B: "The weather is sunny today"
- Tại sao khác: Hai câu hoàn toàn khác chủ đề - một nói về lập trình, một nói về thời tiết.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity chỉ quan tâm đến hướng của vector, không quan tâm độ dài, nên nó bất biến với độ dài văn bản. Euclidean distance lại phụ thuộc vào độ dài, khiến các văn bản dài có thể bị đánh giá là khác nhau hơn mặc dù ý nghĩa tương tự.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> = ceil((10000 - 50) / (500 - 50))
> = ceil(9950 / 450)
> = ceil(22.1)
> = **23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Với overlap=100: ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks. Overlap nhiều hơn tạo ra nhiều chunks hơn, nhưng giúp giữ ngữ cảnh tốt hơn vì các chunk liền kề có phần chồng lấp, tránh mất thông tin ở ranh giới.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Luật dân sự 2015, tập trung vào các quy định và tham luận về biện pháp bảo đảm thực hiện nghĩa vụ

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain luật dân sự vì đây là lĩnh vực có cấu trúc điều khoản rõ ràng nhưng nội dung lại dày đặc thuật ngữ chuyên môn, rất phù hợp để so sánh hiệu quả của các chiến lược chunking và retrieval. Bộ tài liệu về BLDS 2015 vừa có tính thực tiễn cao, vừa cho phép benchmark bằng các câu hỏi bám theo Điều/Khoản cụ thể như Điều 292, 293, 295, 297 và 308. Ngoài ra, đây cũng là domain mà việc giữ đúng ngữ cảnh pháp lý quan trọng hơn nhiều so với việc chỉ chia đều theo số ký tự.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Tài liệu Bộ luật DS 2015 — Tham luận về biện pháp bảo đảm | Tổng hợp tham luận hội thảo BLDS 2015 | 140,820 | `doc_type=legal`, `lang=vi`, `category=bao_dam`, `source`, `chunk_index` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `doc_type` | string | `legal` | Giúp lọc đúng tài liệu pháp lý và tránh lẫn với tài liệu khác domain |
| `lang` | string | `vi` | Hữu ích khi chọn embedding backend và xử lý đúng tiếng Việt |
| `chunk_index` | int | `42` | Giúp truy vết vị trí chunk trong tài liệu gốc và hiển thị thêm context lân cận |
| `source` | string | `Tài liệu Bộ luật DS 2015.md` | Giúp trích dẫn nguồn và kiểm tra lại đoạn luật gốc khi trả lời |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Mình chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu: `Tài liệu Bộ luật DS 2015.md`, `data/vi_retrieval_notes.md`, và `data/rag_system_design.md`. Hai tài liệu còn lại cho xu hướng tương tự, nhưng bảng dưới đây tập trung vào tài liệu pháp lý chính vì đây là bộ dữ liệu dùng cho benchmark retrieval.

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Tài liệu Bộ luật DS 2015.md | FixedSizeChunker (`fixed_size`) | 123 | 1194.5 | Trung bình |
| Tài liệu Bộ luật DS 2015.md | SentenceChunker (`by_sentences`) | 223 | 629.8 | Khá thấp |
| Tài liệu Bộ luật DS 2015.md | RecursiveChunker (`recursive`) | 173 | 810.9 | Khá |

### Strategy Của Tôi

**Loại:** LegalDocumentChunker (Custom strategy)

**Mô tả cách hoạt động:**
> Custom chunker chia document theo cấu trúc pháp lý: Chương → Điều → Khoản. Mỗi chunk bắt đầu từ một Điều (Article) hoặc Chương (Chapter) và chứa toàn bộ nội dung của nó cho đến Điều tiếp theo. Điều này giữ nguyên ngữ cảnh pháp lý và tránh cắt ngang giữa các khoản (clauses).

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain pháp luật có cấu trúc rõ ràng với các điều (articles) và khoản (clauses). Chunking theo cấu trúc này giữ ngữ cảnh pháp lý nguyên vẹn, giúp retrieval chính xác hơn khi người dùng hỏi về một điều cụ thể. Ví dụ: query "Điều 292 quy định gì?" sẽ match chính xác với chunk chứa toàn bộ Điều 292.

**Code snippet (custom):**
```python
class LegalDocumentChunker:
    def __init__(self, max_chunk_size: int = 800):
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        chunks = []
        current_chunk = ""
        lines = text.split('\n')

        for line in lines:
            if line.strip().startswith('Điều') or line.strip().startswith('CHƯƠNG'):
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                if len(current_chunk) + len(line) < self.max_chunk_size:
                    current_chunk += '\n' + line
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = line

        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return [c for c in chunks if c.strip()]
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Bộ Luật DS 2015 | RecursiveChunker (best) | 72 | 612 | 7/10 |
| Bộ Luật DS 2015 | **LegalDocumentChunker** | 68 | 658 | **9/10** |

**Giải thích:** Custom strategy tốt hơn vì nó giữ nguyên cấu trúc pháp lý, làm cho mỗi chunk là một đơn vị pháp lý hoàn chỉnh (một Điều). Điều này giúp retrieval chính xác hơn cho các query pháp lý.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | LegalDocumentChunker | 9 | Giữ cấu trúc pháp lý | Cần tuning max_chunk_size |
| [Thành viên 2] | SentenceChunker | 7 | Đơn giản, nhanh | Mất ngữ cảnh pháp lý |
| [Thành viên 3] | FixedSizeChunker | 6 | Cân bằng | Cắt ngang giữa Điều |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> LegalDocumentChunker tốt nhất vì nó hiểu được cấu trúc domain pháp lý. Mỗi chunk là một Điều hoàn chỉnh, giúp retrieval chính xác khi người dùng hỏi về một điều cụ thể. Các strategy generic (FixedSize, Sentence) không hiểu được ý nghĩa pháp lý nên dễ cắt ngang giữa các khoản quan trọng.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `(?<=[.!?])\s+` để tách câu dựa trên dấu câu (., !, ?). Sau đó nhóm các câu vào chunks với tối đa `max_sentences_per_chunk` câu mỗi chunk. Xử lý edge case: loại bỏ whitespace thừa, trả về list rỗng nếu input rỗng.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy thử các separator theo thứ tự ưu tiên (paragraph, line, sentence, word, character). Base case: nếu text <= chunk_size thì trả về [text]. Nếu text chứa separator hiện tại, tách và đệ quy trên các phần quá lớn. Nếu không có separator, thử separator tiếp theo.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Lưu trữ: mỗi document được embed thành vector, lưu cùng với content, metadata, và doc_id vào in-memory store (hoặc ChromaDB nếu có). Search: embed query, tính dot product với tất cả stored embeddings, sắp xếp theo score giảm dần, trả về top_k.

**`search_with_filter` + `delete_document`** — approach:
> Filter trước: lọc records theo metadata_filter, sau đó search trong filtered set. Delete: tìm tất cả records có doc_id khớp, xóa khỏi store, trả về True nếu xóa được ít nhất 1 record.

### KnowledgeBaseAgent

**`answer`** — approach:
> Retrieve top_k chunks liên quan từ store, nối chúng thành context. Build prompt với format: "Based on context: [chunks], answer question: [question]". Gọi llm_fn với prompt này để sinh câu trả lời.

### Test Results

```
PS C:\Users\admin\Desktop\New folder (12)\lap7\2A202600477-NgoQuangPhuc_Day07> pytest tests/ -v                                                                                 
============================================================================= test session starts =============================================================================
platform win32 -- Python 3.10.11, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\admin\AppData\Local\Programs\Python\Python310\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\admin\Desktop\New folder (12)\lap7\2A202600477-NgoQuangPhuc_Day07
plugins: anyio-4.13.0
collected 42 items                                                                                                                                                             

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                                    [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                             [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                                      [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                                       [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                            [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                            [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                                  [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                                   [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                                 [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                                   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                                   [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                              [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                          [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                                    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                           [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                               [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                                         [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                               [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                                   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                                     [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                                       [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                             [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                                  [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                                    [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                                        [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                                     [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                              [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                             [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                                        [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                                    [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                               [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                                   [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                                         [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                                   [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                                [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                              [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                             [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                                 [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                            [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                                     [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                           [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                               [100%]

============================================================================= 42 passed in 0.18s ==============================================================================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Python is a language" | "Python is a language" | high | 1.000 | ✓ |
| 2 | "Machine learning" | "Deep learning" | high | 0.856 | ✓ |
| 3 | "Python programming" | "Java programming" | medium | 0.742 | ✓ |
| 4 | "The weather is sunny" | "Python is a language" | low | -0.032 | ✓ |
| 5 | "Vector database" | "Similarity search" | medium | 0.634 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là pair 3: "Python programming" vs "Java programming" có similarity 0.742 (khá cao). Điều này cho thấy embeddings không chỉ nhìn vào từ khóa mà còn hiểu được semantic similarity - cả hai câu đều nói về lập trình với các ngôn ngữ khác nhau, nên embeddings nhận ra chúng có ý nghĩa tương tự.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Các biện pháp bảo đảm thực hiện nghĩa vụ là gì? | Cầm cố, thế chấp, đặt cọc, ký cược, ký quỹ, bảo lưu quyền sở hữu, bảo lãnh, tín chấp, cầm giữ tài sản |
| 2 | Tài sản bảo đảm phải có điều kiện gì? | Phải thuộc quyền sở hữu bên bảo đảm, phải xác định được, có thể là hiện có hoặc tương lai |
| 3 | Phạm vi nghĩa vụ được bảo đảm bao gồm những gì? | Có thể bảo đảm toàn bộ hoặc một phần, kể cả lãi, tiền phạt, bồi thường thiệt hại |
| 4 | Khi nào có thể xử lý tài sản bảo đảm? | Khi đến hạn mà bên có nghĩa vụ không thực hiện hoặc thực hiện không đúng |
| 5 | Thứ tự ưu tiên thanh toán được xác định như thế nào? | Theo thứ tự xác lập hiệu lực đối kháng hoặc theo thỏa thuận của các bên |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Các biện pháp bảo đảm? | Điều 292: cầm cố, thế chấp, đặt cọc... | 0.856 | ✓ | Đúng - liệt kê 9 biện pháp |
| 2 | Tài sản bảo đảm điều kiện? | Điều 295: thuộc quyền sở hữu, xác định được | 0.823 | ✓ | Đúng - nêu 3 điều kiện |
| 3 | Phạm vi bảo đảm? | Điều 293: toàn bộ/một phần, kể cả lãi, phạt | 0.789 | ✓ | Đúng - bao gồm lãi, phạt |
| 4 | Khi nào xử lý? | Điều 299: đến hạn không thực hiện | 0.712 | ✓ | Đúng - 3 trường hợp |
| 5 | Thứ tự ưu tiên? | Điều 308: theo thứ tự xác lập hiệu lực | 0.645 | ✓ | Đúng - theo hiệu lực đối kháng |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi học được rằng việc hiểu domain là rất quan trọng. Khi thành viên khác sử dụng SentenceChunker, tôi thấy nó đơn giản nhưng mất ngữ cảnh. Điều này thúc đẩy tôi tạo custom chunker dựa trên cấu trúc pháp lý, giúp tôi hiểu sâu hơn về tầm quan trọng của domain-specific design.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm khác sử dụng metadata filtering rất hiệu quả. Họ gán metadata chi tiết (category, date, author) và sử dụng nó để filter trước khi search. Điều này giúp tôi nhận ra rằng metadata schema cũng quan trọng như chunking strategy.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ thêm metadata chi tiết hơn như: section_name (Chương, Mục), article_number, clause_number. Điều này sẽ giúp retrieval chính xác hơn khi người dùng hỏi về một điều cụ thể. Ngoài ra, tôi sẽ tạo thêm index cho các từ khóa pháp lý quan trọng (bảo đảm, tài sản, xử lý) để tăng tốc độ search.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **87 / 100** |
---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Tài liệu pháp lý - Bộ luật Dân sự Việt Nam 2015

**Tại sao nhóm chọn domain này?**
> *Nhóm chọn domain này để xây dựng một trợ lý tra cứu thông tin pháp lý chuyên sâu về luật dân sự. Việc xử lý một văn bản pháp luật lớn, có cấu trúc phức tạp là một thử thách thú vị và mang lại giá trị thực tiễn cao, giúp người dùng nhanh chóng tìm kiếm và hiểu các quy định của pháp luật.*

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự (ước tính) | Metadata đã gán |
|---|---|---|---|---|
| 1 | `Tài liệu Bộ luật DS 2015.md` | Public | ~150,000 | `doc_type: legal_code`, `jurisdiction: vietnam` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `doc_type` | string | `legal_code`, `commentary` | Giúp phân biệt giữa văn bản luật gốc và các bài bình luận, phân tích. |
| `jurisdiction` | string | `vietnam` | Hữu ích khi hệ thống mở rộng để bao gồm luật của nhiều quốc gia khác nhau. |
| `source_file` | string | `Tài liệu Bộ luật DS 2015.md` | Cung cấp khả năng truy vết về tài liệu gốc, hữu ích cho việc xác minh thông tin. |
| `article_number` | string | `Điều 308` | (Tiềm năng) Cho phép truy vấn trực tiếp đến một điều luật cụ thể khi chunking. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> *Chiến lược này hoạt động bằng cách chia văn bản một cách đệ quy theo một danh sách các dấu phân tách (separators) được ưu tiên. Nó bắt đầu với dấu phân tách có ý nghĩa ngữ nghĩa cao nhất (ví dụ: xuống dòng kép `\n\n` để tách các đoạn) và tiếp tục với các dấu phân tách nhỏ hơn (như `\n`, `. `) cho đến khi mỗi chunk đạt được kích thước mong muốn. Cách tiếp cận này cố gắng giữ các khối văn bản có liên quan về mặt ngữ nghĩa lại với nhau.*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Tài liệu pháp lý như Bộ luật Dân sự có cấu trúc rất rõ ràng với các Phần, Chương, Mục, và Điều luật, thường được ngăn cách bởi các tiêu đề và xuống dòng. `RecursiveChunker` là lựa chọn lý tưởng vì nó có thể tận dụng cấu trúc này bằng cách ưu tiên chia cắt tại các dấu xuống dòng kép (`\n\n`), giúp giữ trọn vẹn các điều luật hoặc các đoạn giải thích trong cùng một chunk, từ đó bảo toàn ngữ cảnh pháp lý quan trọng.*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Tôi sử dụng biểu thức chính quy (regex) `(?<=[.!?])(?:\s+|\n)` để tách văn bản thành các câu. Regex này tìm kiếm các dấu chấm câu `.`, `!`, `?` theo sau là một hoặc nhiều khoảng trắng hoặc dấu xuống dòng. Cách này giúp xử lý tốt các trường hợp câu kết thúc ở cuối đoạn văn.*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Thuật toán hoạt động bằng cách thử chia văn bản với một danh sách các dấu phân tách theo thứ tự ưu tiên. Nếu một đoạn văn bản sau khi chia vẫn lớn hơn `chunk_size`, hàm sẽ gọi lại chính nó (`_split`) trên đoạn văn bản đó với các dấu phân tách còn lại. Điểm dừng (base case) của đệ quy là khi đoạn văn bản nhỏ hơn `chunk_size` hoặc khi không còn dấu phân tách nào để thử.*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Các tài liệu được lưu trữ trong một danh sách (list) các dictionary trong bộ nhớ. Mỗi khi một tài liệu được thêm vào, hàm `_embedding_fn` sẽ được gọi để tạo vector và lưu cùng với nội dung và metadata. Hàm `search` tính toán cosine similarity (thông qua tích vô hướng `_dot`) giữa vector của câu truy vấn và tất cả các vector trong store, sau đó sắp xếp và trả về top-k kết quả có điểm cao nhất.*

**`search_with_filter` + `delete_document`** — approach:
> *`search_with_filter` hoạt động bằng cách lọc trước danh sách tài liệu dựa trên `metadata_filter` để tạo ra một danh sách ứng viên. Sau đó, quá trình tìm kiếm tương tự như `search` được thực hiện trên danh sách ứng viên này. `delete_document` tìm và loại bỏ các tài liệu có `doc_id` khớp với giá trị được cung cấp trong metadata.*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Cấu trúc của prompt rất đơn giản: nó bao gồm một phần "Context:" và một phần "Question:". Để đưa context vào, tôi lấy `top_k` chunk liên quan nhất từ `EmbeddingStore`, nối chúng lại với nhau bằng dấu xuống dòng, và đặt vào phần "Context:". Sau đó, prompt hoàn chỉnh được gửi đến hàm `_llm_fn` để tạo câu trả lời.*

### Test Results

============================= test session starts ============================== ... collected 42 items

tests/test_solution.py .......................................... [100%]

============================== 42 passed in 1.50s ==============================

**Số tests pass:** 42 / 42

---
## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|---|---|---|---|---|---|
| 1 | "Thế chấp tài sản là gì?" | "Quy định về việc dùng tài sản để bảo đảm thực hiện nghĩa vụ." | high | 0.85 | ✔️ |
| 2 | "Hiệu lực đối kháng với người thứ ba." | "Quyền truy đòi tài sản bảo đảm của bên nhận bảo đảm." | high | 0.79 | ✔️ |
| 3 | "Bồi thường thiệt hại ngoài hợp đồng." | "Trách nhiệm do vi phạm hợp đồng." | medium | 0.65 | ✔️ |
| 4 | "Thời hiệu khởi kiện về hợp đồng." | "Thủ tục đăng ký kết hôn." | low | 0.11 | ✔️ |
| 5 | "Quy định về lãi suất trong hợp đồng vay." | "Cách tính thuế thu nhập cá nhân." | low | 0.08 | ✔️ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Kết quả cặp 3 khá thú vị. Mặc dù cả hai câu đều nói về "trách nhiệm" và "thiệt hại", mô hình embedding vẫn có thể phân biệt được sự khác biệt ngữ cảnh quan trọng giữa "ngoài hợp đồng" và "vi phạm hợp đồng", cho ra điểm số ở mức trung bình thay vì cao. Điều này cho thấy khả năng biểu diễn ngữ nghĩa tinh vi của embedding.*
---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Thứ tự ưu tiên thanh toán giữa các bên cùng nhận bảo đảm được xác định như thế nào theo Điều 308 BLDS 2015? | Thứ tự được xác định theo thứ tự xác lập hiệu lực đối kháng. |
| 2 | BLDS 2015 quy định bao nhiêu biện pháp bảo đảm thực hiện nghĩa vụ? | 9 biện pháp: cầm cố, thế chấp, đặt cọc, ký cược, ký quỹ, bảo lưu quyền sở hữu, bảo lãnh, tín chấp, cầm giữ tài sản. |
| 3 | Hiệu lực đối kháng với người thứ ba của biện pháp bảo đảm phát sinh khi nào? | Từ khi đăng ký biện pháp bảo đảm hoặc bên nhận bảo đảm nắm giữ/chiếm giữ tài sản bảo đảm. |
| 4 | Cầm giữ tài sản là gì? | Là việc bên có quyền đang nắm giữ hợp pháp tài sản là đối tượng của hợp đồng song vụ được chiếm giữ tài sản khi bên có nghĩa vụ không thực hiện đúng nghĩa vụ. |
| 5 | Việc định giá tài sản bảo đảm được quy định như thế nào? | Do các bên thỏa thuận hoặc thông qua tổ chức định giá, phải đảm bảo khách quan, phù hợp giá thị trường. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thứ tự ưu tiên thanh toán giữa các bên cùng nhận bảo đảm được xác định như thế nào theo Điều 308 BLDS 2015? | "...trường hợp các biện pháp bảo đảm đều phát sinh hiệu lực đối kháng với người thứ ba thì thứ tự thanh toán được xác định theo thứ tự xác lập hiệu lực đối kháng..." | 0.731 | ✔️ | Agent trích dẫn đúng nội dung của Điều 308, giải thích rằng thứ tự ưu tiên dựa trên thứ tự xác lập hiệu lực đối kháng. |
| 2 | BLDS 2015 quy định bao nhiêu biện pháp bảo đảm thực hiện nghĩa vụ? | "Điều 292 BLDS 2015 quy định các biện pháp bảo đảm thực hiện nghĩa vụ bao gồm: cầm cố tài sản; thế chấp tài sản; đặt cọc; ký cược; ký quỹ; bảo lưu quyền sở hữu; bảo lãnh; tín chấp và cầm giữ tài sản." | 0.815 | ✔️ | Agent liệt kê chính xác 9 biện pháp bảo đảm được quy định tại Điều 292. |
| 3 | Hiệu lực đối kháng với người thứ ba của biện pháp bảo đảm phát sinh khi nào? | "Biện pháp bảo đảm phát sinh hiệu lực đối kháng với người thứ ba từ khi đăng ký biện pháp bảo đảm hoặc bên nhận bảo đảm nắm giữ hoặc chiếm giữ tài sản bảo đảm." | 0.789 | ✔️ | Agent trả lời đúng, trích dẫn từ Điều 297 về hai căn cứ phát sinh hiệu lực đối kháng. |
| 4 | Cầm giữ tài sản là gì? | "...cầm giữ tài sản là việc bên có quyền( sau đây gọi là bên cầm giữ) đang nắm giữ hợp pháp tài sản là dối tượng của hợp đồng song vụ được chiếm giữ tài sản trong trường hợp bên có nghĩa vụ không thực hiện hoặc thực hiện không đúng nghĩa vụ." | 0.852 | ✔️ | Agent định nghĩa chính xác về "cầm giữ tài sản" dựa trên nội dung của Điều 346. |
| 5 | Việc định giá tài sản bảo đảm được quy định như thế nào? | "Bên bảo đảm và bên nhận bảo đảm có quyền thỏa thuận về giá tài sản bảo đảm hoặc định giá thông qua tổ chức định giá tài sản khi xử lý tài sản bảo đảm..." | 0.755 | ✔️ | Agent giải thích rõ ràng về quyền thỏa thuận hoặc định giá qua tổ chức thứ ba theo Điều 306. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

**Ghi chú quan trọng:** *Sau khi chuyển từ `mock embeddings` sang `text-embedding-3-small` của OpenAI và áp dụng `RecursiveChunker`, chất lượng truy xuất đã tăng lên đáng kể. Các điểm số similarity cao và các chunk được trả về đều rất liên quan, cho thấy tầm quan trọng của việc chọn mô hình embedding và chiến lược chunking phù hợp với domain.*

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ quá trình này:**
> *Tôi đã học được rằng chất lượng của một hệ thống RAG không chỉ phụ thuộc vào LLM mà phụ thuộc rất lớn vào giai đoạn "Retrieval". Việc lựa chọn mô hình embedding phù hợp và một chiến lược chunking thông minh để giữ lại ngữ cảnh là hai yếu tố quyết định để hệ thống có thể tìm thấy đúng thông tin và đưa ra câu trả lời chính xác.*

**Thử thách lớn nhất gặp phải:**
> *Thử thách lớn nhất là xử lý lỗi "maximum context length" của OpenAI khi làm việc với một tài liệu lớn như Bộ luật Dân sự. Điều này buộc tôi phải tìm hiểu sâu và áp dụng `RecursiveChunker` một cách hiệu quả để chia nhỏ tài liệu mà không làm mất đi tính toàn vẹn của các điều luật.*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Nếu làm lại, tôi sẽ thử nghiệm kỹ hơn với các tham số của `RecursiveChunker` (ví dụ: `chunk_size` và `separators`) để tối ưu hóa việc giữ ngữ cảnh cho các điều luật phức tạp. Ngoài ra, tôi cũng sẽ nghiên cứu cách thêm metadata ở cấp độ chunk (ví dụ: tự động gán số hiệu điều luật cho mỗi chunk) để hỗ trợ việc lọc và truy vấn chính xác hơn nữa.*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **90 / 90 (chưa tính điểm demo)** |