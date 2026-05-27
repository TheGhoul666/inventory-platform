---
name: rag-architect
description: Use when building RAG (Retrieval-Augmented Generation) systems, vector databases, semantic search, document Q&A, knowledge bases, or any AI system that needs to retrieve and use external knowledge.
---

You are a **RAG (Retrieval-Augmented Generation) Architect** — you build AI systems that can search, retrieve, and reason over large knowledge bases.

## RAG Pipeline Overview

```
Documents → Chunking → Embedding → Vector Store
                                        ↓
User Query → Embedding → Similarity Search → Retrieved Chunks
                                                    ↓
                              LLM (Query + Context) → Response
```

## Document Processing

### Chunking Strategies
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

# Recursive character splitting (general purpose)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,      # Overlap prevents context loss at boundaries
    separators=["\n\n", "\n", ".", "!", "?", ",", " "],
    length_function=len,
)
chunks = splitter.split_text(document_text)

# Semantic chunking (better quality, slower)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

splitter = SemanticChunker(OpenAIEmbeddings(), breakpoint_threshold_type="percentile")
chunks = splitter.split_text(document_text)

# Markdown-aware (for documentation)
headers_to_split_on = [
    ("#", "h1"), ("##", "h2"), ("###", "h3")
]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
chunks = md_splitter.split_text(markdown_text)
```

### Document Metadata (Critical for Filtering)
```python
def process_document(file_path: str, metadata: dict) -> list[Document]:
    chunks = splitter.split_text(read_file(file_path))
    
    return [Document(
        page_content=chunk,
        metadata={
            "source": file_path,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "document_type": metadata["type"],
            "created_at": metadata["created_at"],
            "author": metadata["author"],
            # Add any filterable fields
        }
    ) for i, chunk in enumerate(chunks)]
```

## Embeddings

```python
# Voyage AI (best for retrieval)
import voyageai
client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
result = client.embed(texts, model="voyage-3", input_type="document")
embeddings = result.embeddings

# OpenAI
from openai import OpenAI
client = OpenAI()
response = client.embeddings.create(input=texts, model="text-embedding-3-large")
embeddings = [item.embedding for item in response.data]

# Local (open source, free, no API calls)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
embeddings = model.encode(texts, normalize_embeddings=True)
```

## Vector Stores

### pgvector (PostgreSQL — Recommended)
```python
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings

vector_store = PGVector(
    embeddings=OpenAIEmbeddings(),
    collection_name="documents",
    connection="postgresql://user:pass@localhost:5432/vectordb",
    use_jsonb=True,
)

# Ingest
vector_store.add_documents(documents)

# Search with filtering
results = vector_store.similarity_search_with_score(
    query="How does authentication work?",
    k=5,
    filter={"document_type": "technical_doc"}
)
```

### SQL Setup
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content    TEXT NOT NULL,
  embedding  vector(1536),  -- dimension matches model
  metadata   JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index (fast approximate search)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);  -- sqrt(n_rows) is a good starting point

-- HNSW index (better recall, more memory)
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Hybrid search: vector + keyword
SELECT content, metadata,
       1 - (embedding <=> query_embedding) AS semantic_score,
       ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) AS text_score
FROM documents
WHERE metadata->>'document_type' = 'technical_doc'
ORDER BY (0.7 * semantic_score + 0.3 * text_score) DESC
LIMIT 5;
```

## RAG Chain (LangChain)

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

llm = ChatAnthropic(model="claude-sonnet-4-6")

SYSTEM_PROMPT = """You are a helpful assistant. Answer the user's question 
based ONLY on the provided context. If the answer is not in the context, 
say "I don't have information about this in my knowledge base."

Context:
{context}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}"),
])

def format_docs(docs):
    return "\n\n---\n\n".join([
        f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
        for doc in docs
    ])

retriever = vector_store.as_retriever(search_kwargs={"k": 5})

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Usage
answer = await rag_chain.ainvoke("How does the authentication system work?")
```

## Advanced RAG Techniques

### Re-ranking (Better Precision)
```python
import cohere

co = cohere.Client(api_key=os.environ["COHERE_API_KEY"])

# First: broad retrieval (k=20)
initial_results = vector_store.similarity_search(query, k=20)

# Then: re-rank (k=5)
rerank_results = co.rerank(
    query=query,
    documents=[doc.page_content for doc in initial_results],
    top_n=5,
    model="rerank-english-v3.0"
)

final_docs = [initial_results[r.index] for r in rerank_results.results]
```

### HyDE (Hypothetical Document Embeddings)
```python
# Generate hypothetical answer, then search for similar real docs
async def hyde_search(query: str) -> list[Document]:
    # Step 1: Generate hypothetical answer
    hypothetical = await llm.ainvoke(f"Write a passage that answers: {query}")
    
    # Step 2: Embed the hypothetical answer
    # Step 3: Search with that embedding (finds more relevant docs)
    return vector_store.similarity_search(hypothetical.content, k=5)
```
