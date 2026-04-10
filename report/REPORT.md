# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

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

**Domain:** [ví dụ: Customer support FAQ, Vietnamese law, cooking recipes, ...]

**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:*

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Strategy Của Tôi

**Loại:** [FixedSizeChunker / SentenceChunker / RecursiveChunker / custom strategy]

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **của tôi** | | | |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*

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
42 passed in 0.24s
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
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
