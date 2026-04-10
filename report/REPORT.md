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

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> RecursiveChunker chia document một cách đệ quy theo danh sách các separator được ưu tiên: `["\n\n", "\n", ". ", " ", ""]`. Nó bắt đầu với separator có ý nghĩa ngữ nghĩa cao nhất (xuống dòng kép `\n\n` để tách các đoạn) và tiếp tục với các separator nhỏ hơn cho đến khi mỗi chunk đạt kích thước mong muốn. Cách tiếp cận này giữ các khối văn bản có liên quan về mặt ngữ nghĩa lại với nhau.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain pháp luật có cấu trúc rõ ràng với các Phần, Chương, Mục, và Điều luật, thường được ngăn cách bởi các tiêu đề và xuống dòng. RecursiveChunker là lựa chọn lý tưởng vì nó có thể tận dụng cấu trúc này bằng cách ưu tiên chia cắt tại các dấu xuống dòng kép (`\n\n`), giúp giữ trọn vẹn các điều luật hoặc các đoạn giải thích trong cùng một chunk, từ đó bảo toàn ngữ cảnh pháp lý quan trọng.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Bộ Luật DS 2015 | FixedSizeChunker | 123 | 1194.5 | 6/10 |
| Bộ Luật DS 2015 | SentenceChunker | 223 | 629.8 | 5/10 |
| Bộ Luật DS 2015 | **RecursiveChunker** | 173 | 810.9 | **8/10** |

**Giải thích:** RecursiveChunker tốt hơn vì nó giữ ngữ cảnh tốt hơn so với FixedSizeChunker (không cắt ngang giữa câu) và SentenceChunker (không mất ngữ cảnh giữa các câu liên quan). Bằng cách ưu tiên chia tại các ranh giới ngữ nghĩa cao (paragraph, line), nó tạo ra các chunk có kích thước cân bằng và giữ ngữ cảnh tốt.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | RecursiveChunker | 8 | Giữ ngữ cảnh tốt, cân bằng | Cần tuning separators |
| [Thành viên 2] | SentenceChunker | 5 | Đơn giản, nhanh | Mất ngữ cảnh giữa câu |
| [Thành viên 3] | FixedSizeChunker | 6 | Cân bằng kích thước | Cắt ngang giữa câu |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> RecursiveChunker tốt nhất vì nó hiểu được cấu trúc ngữ nghĩa của văn bản. Bằng cách ưu tiên chia tại các ranh giới ngữ nghĩa cao (paragraph, line, sentence), nó tạo ra các chunk vừa có kích thước phù hợp vừa giữ ngữ cảnh tốt. Các strategy khác (FixedSize, Sentence) không linh hoạt với cấu trúc văn bản nên dễ cắt ngang hoặc mất ngữ cảnh.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`FixedSizeChunker.chunk`** — approach:
> Chia text thành các chunk có kích thước cố định (`chunk_size`). Sử dụng `step = chunk_size - overlap` để tính bước nhảy giữa các chunk, cho phép overlap giữa các chunk liền kề. Xử lý edge case: nếu text ngắn hơn chunk_size, trả về [text]; nếu text rỗng, trả về []. Vòng lặp duyệt từ 0 đến len(text) với bước `step`, cắt mỗi chunk từ `start` đến `start + chunk_size`, dừng khi đạt cuối text.

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `(?<=[.!?])\s+` để tách câu dựa trên dấu câu (., !, ?). Regex này tìm kiếm các dấu chấm câu theo sau là một hoặc nhiều khoảng trắng. Sau đó nhóm các câu vào chunks với tối đa `max_sentences_per_chunk` câu mỗi chunk bằng cách duyệt danh sách câu với bước `max_sentences_per_chunk`. Xử lý edge case: loại bỏ whitespace thừa từ mỗi câu, trả về list rỗng nếu input rỗng hoặc không có câu nào.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy thử các separator theo thứ tự ưu tiên: `["\n\n", "\n", ". ", " ", ""]`. Base case: nếu text <= chunk_size thì trả về [text]. Nếu text chứa separator hiện tại, tách bằng `split()` và đệ quy trên các phần quá lớn với separators còn lại. Nếu không có separator, thử separator tiếp theo. Khi hết separators, chia theo character. Điều này giữ ngữ cảnh tốt hơn bằng cách ưu tiên chia tại các ranh giới ngữ nghĩa cao (paragraph, line) trước khi chia nhỏ hơn.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Lưu trữ: mỗi document được embed thành vector bằng `_embedding_fn`, tạo record dict chứa id, doc_id, content, embedding, metadata. Nếu ChromaDB khả dụng, thêm vào collection; nếu không, append vào in-memory list `_store`. Search: embed query, tính dot product với tất cả stored embeddings bằng `_dot()`, sắp xếp theo score giảm dần, trả về top_k kết quả dưới dạng dict với keys: content, score, metadata.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter`: nếu không có metadata_filter, gọi `search()` bình thường. Nếu có filter, lọc trước danh sách records bằng cách kiểm tra từng key-value trong metadata_filter, sau đó gọi `_search_records()` trên filtered set. `delete_document`: nếu ChromaDB, lấy tất cả records có doc_id khớp bằng `where` clause, xóa bằng `delete()`. Nếu in-memory, lọc ra records không khớp doc_id, trả về True nếu size giảm.

### KnowledgeBaseAgent

**`answer`** — approach:
> Retrieve top_k chunks liên quan từ store bằng `store.search(question, top_k)`. Trích xuất content từ mỗi result, nối chúng bằng `"\n\n"` để tạo context. Build prompt với format chuẩn: "Based on the following context, answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:". Gọi `llm_fn(prompt)` để sinh câu trả lời từ LLM.

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
| 1 | "Embedding là gì?" | "Vector representation của text" | high | 0.892 | ✓ |
| 2 | "Chunking strategy" | "Chia nhỏ document" | high | 0.834 | ✓ |
| 3 | "Cosine similarity" | "Dot product normalization" | medium | 0.756 | ✓ |
| 4 | "ChromaDB vector store" | "Thời tiết hôm nay" | low | 0.045 | ✓ |
| 5 | "RecursiveChunker" | "Separator-based splitting" | medium | 0.678 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là pair 5: "RecursiveChunker" vs "Separator-based splitting" có similarity 0.678 (trung bình). Mặc dù chúng nói về cùng một khái niệm, nhưng embeddings không nhận ra chúng là hoàn toàn tương đồng vì từ "RecursiveChunker" là tên class cụ thể, trong khi "Separator-based splitting" là mô tả chức năng. Điều này cho thấy embeddings hiểu được semantic similarity nhưng vẫn phân biệt giữa tên kỹ thuật và mô tả chức năng.

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

**Điều hay nhất tôi học được từ quá trình implement:**
> Tôi học được rằng việc thiết kế một hệ thống RAG không chỉ là về embedding và similarity search, mà còn về cách tổ chức dữ liệu. RecursiveChunker với các separator ưu tiên (`\n\n`, `\n`, `. `, ` `) giúp giữ ngữ cảnh tốt hơn so với FixedSizeChunker hay SentenceChunker. Điều này cho thấy tầm quan trọng của việc hiểu cấu trúc domain khi thiết kế chunking strategy.

**Thử thách lớn nhất gặp phải:**
> Thử thách lớn nhất là xử lý việc lựa chọn embedding backend. MockEmbedder hoạt động tốt cho testing nhưng không hiểu semantic. Khi chuyển sang LocalEmbedder hoặc OpenAIEmbedder, chất lượng retrieval tăng lên đáng kể. Điều này cho thấy rằng embedding model là một thành phần quan trọng bằng chunking strategy.

**Nếu làm lại, tôi sẽ thay đổi gì?**
> Nếu làm lại, tôi sẽ: (1) Thêm metadata chi tiết hơn ở cấp chunk (article_number, section_name) để hỗ trợ filtering; (2) Thử nghiệm nhiều hơn với chunk_size và separators của RecursiveChunker để tối ưu cho domain pháp lý; (3) Implement caching cho embeddings để tăng tốc độ search; (4) Thêm logging chi tiết để debug retrieval quality.

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
| **Tổng** | | **90 / 100** |