# TRD (Technical Requirements Document)
# 바이오 RAG 논문 분석 플랫폼

**문서 버전**: 1.0  
**작성일**: 2024년 12월  
**프로젝트명**: Bio-RAG (Biomedical Research AI-Guided Analytics)

---

## 1. System Overview

### 1.1 Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Web UI      │  │  Mobile UI   │  │  API Client  │              │
│  │  (React.js)  │  │  (Responsive)│  │  (REST/SDK)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS
┌─────────────────────────────────────────────────────────────────────┐
│                      Application Layer                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  API Gateway (FastAPI)                                       │  │
│  │  - Authentication/Authorization                              │  │
│  │  - Rate Limiting                                             │  │
│  │  - Request Routing                                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  Search     │  │  RAG        │  │  Analytics  │               │
│  │  Service    │  │  Service    │  │  Service    │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       Data Processing Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Data        │  │  Embedding   │  │  Batch       │             │
│  │  Collector   │  │  Generator   │  │  Processor   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  PostgreSQL  │  │  Vector DB   │  │  Object      │             │
│  │  (Metadata)  │  │  (Chroma)    │  │  Storage(S3) │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  PubMed API  │  │  OpenAI API  │  │  Monitoring  │             │
│  │              │  │  (GPT-4)     │  │  (DataDog)   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | React.js | 18.2+ | UI Framework |
| | TypeScript | 5.0+ | Type Safety |
| | TailwindCSS | 3.3+ | Styling |
| | Recharts | 2.5+ | Data Visualization |
| | React Query | 4.0+ | State Management |
| **Backend** | Python | 3.11+ | Primary Language |
| | FastAPI | 0.104+ | Web Framework |
| | Pydantic | 2.0+ | Data Validation |
| | Celery | 5.3+ | Task Queue |
| | Redis | 7.0+ | Caching/Queue |
| **AI/ML** | LangChain | 0.1+ | RAG Framework |
| | Hugging Face | 4.35+ | Model Loading |
| | BioBERT | - | Domain Embedding |
| | PubMedBERT | - | Medical NLP |
| | OpenAI API | GPT-4 | LLM Backend |
| **Database** | PostgreSQL | 15+ | Relational DB |
| | ChromaDB | 0.4+ | Vector DB |
| | FAISS | 1.7+ | Vector Search |
| **Storage** | AWS S3 | - | Object Storage |
| | MinIO | - | Local Dev |
| **DevOps** | Docker | 24.0+ | Containerization |
| | Kubernetes | 1.28+ | Orchestration |
| | GitHub Actions | - | CI/CD |
| | Terraform | 1.5+ | IaC |
| **Monitoring** | Prometheus | 2.45+ | Metrics |
| | Grafana | 10.0+ | Visualization |
| | Sentry | - | Error Tracking |

---

## 2. System Components

### 2.1 Data Collection Module

#### 2.1.1 PubMed API Integration

**Specification**:
```python
class PubMedCollector:
    """
    PubMed API 기반 논문 메타데이터 수집
    """
    
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = os.getenv("PUBMED_API_KEY")
        self.rate_limit = 10  # requests per second (with API key)
    
    async def search_papers(
        self,
        query: str,
        max_results: int = 100,
        date_range: Optional[tuple] = None
    ) -> List[PaperMetadata]:
        """
        논문 검색 및 메타데이터 수집
        
        Args:
            query: 검색 쿼리 (예: "cancer immunotherapy[Title/Abstract]")
            max_results: 최대 결과 수
            date_range: (start_date, end_date) in YYYY/MM/DD format
            
        Returns:
            List of PaperMetadata objects
        """
        pass
    
    async def fetch_abstract(self, pmid: str) -> str:
        """PMID로 초록 가져오기"""
        pass
    
    async def batch_fetch(self, pmid_list: List[str]) -> List[dict]:
        """여러 논문을 배치로 가져오기 (rate limiting 적용)"""
        pass
```

**Data Model**:
```python
from pydantic import BaseModel
from datetime import datetime

class PaperMetadata(BaseModel):
    pmid: str  # PubMed ID
    title: str
    abstract: str
    authors: List[str]
    journal: str
    publication_date: datetime
    doi: Optional[str]
    keywords: List[str]
    mesh_terms: List[str]  # Medical Subject Headings
    citation_count: Optional[int]
    pdf_url: Optional[str]
```

**API Endpoints**:
- `esearch.fcgi`: 논문 검색
- `efetch.fcgi`: 메타데이터 가져오기
- `elink.fcgi`: 관련 논문 링크

**Error Handling**:
```python
class PubMedAPIError(Exception):
    pass

# Retry logic with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def api_call_with_retry(url: str):
    """API 호출 재시도 로직"""
    pass
```

#### 2.1.2 PDF Processing

**Library**: PyPDF2, pdfplumber

**Workflow**:
```python
class PDFProcessor:
    
    def extract_text(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        pass
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        논문 섹션 분리
        
        Returns:
            {
                'abstract': '...',
                'introduction': '...',
                'methods': '...',
                'results': '...',
                'discussion': '...',
                'references': '...'
            }
        """
        # Regex patterns for section headers
        patterns = {
            'abstract': r'ABSTRACT',
            'introduction': r'INTRODUCTION|1\.|I\.',
            'methods': r'METHODS|MATERIALS AND METHODS',
            ...
        }
        pass
```

**Text Cleaning**:
```python
def clean_text(text: str) -> str:
    """
    텍스트 정제
    - 특수문자 제거
    - 연속 공백 제거
    - 참조 번호 제거 ([1], [2] 등)
    - 표/그림 캡션 제거
    """
    # Remove page numbers
    text = re.sub(r'\n\d+\n', '\n', text)
    
    # Remove reference numbers
    text = re.sub(r'\[\d+\]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

#### 2.1.3 Batch Processing

**Scheduler**: APScheduler or Celery Beat

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('bio_rag', broker='redis://localhost:6379')

@app.task
def daily_paper_crawl():
    """
    매일 새 논문 크롤링 (UTC 02:00)
    """
    keywords = ['cancer immunotherapy', 'CRISPR', 'CAR-T']
    
    for keyword in keywords:
        papers = pubmed_collector.search_papers(
            query=keyword,
            date_range=('yesterday', 'today')
        )
        
        for paper in papers:
            # Save to DB
            db.save_paper(paper)
            
            # Generate embeddings
            process_paper_async.delay(paper.pmid)

@app.task
def process_paper_async(pmid: str):
    """비동기 논문 처리"""
    # 1. Fetch full text
    # 2. Generate chunks
    # 3. Generate embeddings
    # 4. Store in vector DB
    pass

# Schedule
app.conf.beat_schedule = {
    'daily-crawl': {
        'task': 'tasks.daily_paper_crawl',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

---

### 2.2 Embedding & Vector DB Module

#### 2.2.1 Embedding Model Selection

**Model Comparison**:

| Model | Dimensions | Pros | Cons | Use Case |
|-------|------------|------|------|----------|
| BioBERT-v1.1 | 768 | 생명과학 특화 | 2019년 모델 | 바이오 용어 |
| PubMedBERT | 768 | PubMed 학습 | 영문만 지원 | 논문 전문 |
| SciBERT | 768 | 과학 논문 특화 | 범용 과학 | 일반 과학 |
| text-embedding-ada-002 | 1536 | 고성능, API | 비용 발생 | 프로토타입 |

**Selected Model**: PubMedBERT (microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract)

**Implementation**:
```python
from transformers import AutoTokenizer, AutoModel
import torch

class EmbeddingGenerator:
    
    def __init__(self, model_name: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        
        # GPU if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
    
    def encode(self, text: str, max_length: int = 512) -> np.ndarray:
        """
        텍스트를 768차원 벡터로 변환
        
        Args:
            text: 입력 텍스트
            max_length: 최대 토큰 길이
            
        Returns:
            numpy array (768,)
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            max_length=max_length,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        ).to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use [CLS] token embedding
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        
        return embedding.squeeze()
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """배치 인코딩"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = [self.encode(text) for text in batch]
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
```

#### 2.2.2 Text Chunking Strategy

**Chunking Methods**:

1. **Fixed-size chunking** (기본)
```python
def chunk_by_tokens(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    고정 토큰 수로 청킹
    
    Args:
        text: 입력 텍스트
        chunk_size: 청크 크기 (토큰 수)
        overlap: 청크 간 겹침 (토큰 수)
    """
    tokens = tokenizer.tokenize(text)
    chunks = []
    
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = tokenizer.convert_tokens_to_string(chunk_tokens)
        chunks.append(chunk_text)
    
    return chunks
```

2. **Section-based chunking** (논문용)
```python
def chunk_by_section(paper: PaperMetadata) -> List[Chunk]:
    """
    논문 섹션별 청킹
    
    Returns:
        [
            Chunk(text=abstract, section='abstract', ...),
            Chunk(text=methods, section='methods', ...),
            ...
        ]
    """
    sections = extract_sections(paper.full_text)
    
    chunks = []
    for section_name, section_text in sections.items():
        # Sub-chunk if too long
        if len(section_text) > 2000:
            sub_chunks = chunk_by_tokens(section_text)
            for i, sub_chunk in enumerate(sub_chunks):
                chunks.append(Chunk(
                    text=sub_chunk,
                    section=f"{section_name}_{i}",
                    pmid=paper.pmid,
                    title=paper.title
                ))
        else:
            chunks.append(Chunk(
                text=section_text,
                section=section_name,
                pmid=paper.pmid,
                title=paper.title
            ))
    
    return chunks
```

**Chunk Data Model**:
```python
class Chunk(BaseModel):
    id: str  # UUID
    pmid: str
    title: str
    text: str
    section: str  # 'abstract', 'introduction', etc.
    embedding: Optional[List[float]] = None
    metadata: dict  # journal, date, authors, etc.
```

#### 2.2.3 Vector Database

**Option 1: ChromaDB** (Recommended for MVP)

```python
import chromadb
from chromadb.config import Settings

class VectorStore:
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name="biomedical_papers",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
    
    def add_chunks(self, chunks: List[Chunk], embeddings: np.ndarray):
        """청크를 벡터 DB에 저장"""
        self.collection.add(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings.tolist(),
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    'pmid': chunk.pmid,
                    'title': chunk.title,
                    'section': chunk.section,
                    **chunk.metadata
                }
                for chunk in chunks
            ]
        )
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_dict: Optional[dict] = None
    ) -> List[dict]:
        """
        유사 청크 검색
        
        Args:
            query_embedding: 쿼리 벡터
            top_k: 상위 K개 결과
            filter_dict: 메타데이터 필터 (예: {'section': 'abstract'})
            
        Returns:
            [
                {
                    'id': '...',
                    'text': '...',
                    'distance': 0.85,
                    'metadata': {...}
                },
                ...
            ]
        """
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=filter_dict
        )
        
        return self._format_results(results)
```

**Option 2: FAISS** (For Scale)

```python
import faiss

class FAISSVectorStore:
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        
        # Index type: Inner Product (cosine similarity)
        self.index = faiss.IndexFlatIP(dimension)
        
        # For larger datasets, use IVF
        # quantizer = faiss.IndexFlatIP(dimension)
        # self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist=100)
        
        self.id_map = {}  # index -> chunk_id mapping
    
    def add_vectors(self, embeddings: np.ndarray, chunk_ids: List[str]):
        """벡터 추가"""
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Update ID mapping
        for i, chunk_id in enumerate(chunk_ids):
            self.id_map[start_idx + i] = chunk_id
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[tuple]:
        """
        검색
        
        Returns:
            [(chunk_id, distance), ...]
        """
        faiss.normalize_L2(query_embedding.reshape(1, -1))
        
        distances, indices = self.index.search(query_embedding.reshape(1, -1), top_k)
        
        results = [
            (self.id_map[idx], float(dist))
            for idx, dist in zip(indices[0], distances[0])
        ]
        
        return results
    
    def save_index(self, path: str):
        """인덱스 저장"""
        faiss.write_index(self.index, path)
    
    def load_index(self, path: str):
        """인덱스 로드"""
        self.index = faiss.read_index(path)
```

**Hybrid Approach**:
- ChromaDB: 메타데이터 검색 + 작은 규모
- FAISS: 고속 벡터 검색 + 대규모
- PostgreSQL: 메타데이터 관리

---

### 2.3 RAG Service

#### 2.3.1 RAG Pipeline Architecture

```python
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

class RAGService:
    
    def __init__(
        self,
        vector_store: VectorStore,
        llm_api_key: str,
        model_name: str = "gpt-4"
    ):
        self.vector_store = vector_store
        self.embedding_generator = EmbeddingGenerator()
        
        # LLM setup
        self.llm = OpenAI(
            api_key=llm_api_key,
            model_name=model_name,
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=1000
        )
        
        # Prompt template
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> PromptTemplate:
        """프롬프트 템플릿 생성"""
        template = """
You are an expert biomedical researcher assistant. Answer the question based on the provided research paper excerpts.

IMPORTANT RULES:
1. Only use information from the provided context
2. Cite sources using [PMID: xxxxx] format
3. If the context doesn't contain enough information, say "I cannot find sufficient information in the provided papers"
4. Do not make assumptions or add information not present in the context

Context from research papers:
{context}

Question: {question}

Provide a detailed answer with citations:
"""
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    async def query(
        self,
        question: str,
        top_k: int = 5,
        rerank: bool = True
    ) -> RAGResponse:
        """
        RAG 기반 질의응답
        
        Workflow:
        1. Question Embedding
        2. Vector Search
        3. Re-ranking (optional)
        4. Prompt Construction
        5. LLM Call
        6. Response Validation
        """
        
        # 1. Embed question
        question_embedding = self.embedding_generator.encode(question)
        
        # 2. Search similar chunks
        search_results = self.vector_store.search(
            query_embedding=question_embedding,
            top_k=top_k * 2 if rerank else top_k
        )
        
        # 3. Re-ranking (optional)
        if rerank:
            search_results = self._rerank_results(question, search_results)[:top_k]
        
        # 4. Build context
        context = self._build_context(search_results)
        
        # 5. Generate prompt
        prompt = self.prompt_template.format(
            context=context,
            question=question
        )
        
        # 6. Call LLM
        answer = await self.llm.agenerate([prompt])
        
        # 7. Validate response (hallucination check)
        validation_result = self._validate_response(answer, search_results)
        
        return RAGResponse(
            answer=answer,
            sources=self._extract_sources(search_results),
            confidence=validation_result.confidence,
            chunks_used=search_results
        )
    
    def _build_context(self, search_results: List[dict]) -> str:
        """검색 결과로 컨텍스트 구성"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            pmid = result['metadata']['pmid']
            title = result['metadata']['title']
            text = result['text']
            
            context_parts.append(
                f"[Paper {i}] PMID: {pmid}\n"
                f"Title: {title}\n"
                f"Content: {text}\n"
            )
        
        return "\n\n".join(context_parts)
    
    def _rerank_results(self, question: str, results: List[dict]) -> List[dict]:
        """
        교차 인코더를 사용한 재랭킹
        
        Uses: sentence-transformers/ms-marco-MiniLM-L-12-v2
        """
        from sentence_transformers import CrossEncoder
        
        model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
        
        # Create (question, passage) pairs
        pairs = [(question, r['text']) for r in results]
        
        # Score pairs
        scores = model.predict(pairs)
        
        # Sort by score
        ranked_results = [
            result for _, result in sorted(
                zip(scores, results),
                key=lambda x: x[0],
                reverse=True
            )
        ]
        
        return ranked_results
    
    def _validate_response(self, answer: str, sources: List[dict]) -> ValidationResult:
        """
        응답 검증 (할루시네이션 체크)
        
        Methods:
        1. Source attribution check
        2. Factual consistency check
        3. Confidence scoring
        """
        # Extract PMIDs from answer
        cited_pmids = re.findall(r'PMID:\s*(\d+)', answer)
        
        # Check if cited PMIDs are in sources
        source_pmids = [s['metadata']['pmid'] for s in sources]
        valid_citations = all(pmid in source_pmids for pmid in cited_pmids)
        
        # Confidence score (0-1)
        confidence = 0.9 if valid_citations else 0.5
        
        return ValidationResult(
            is_valid=valid_citations,
            confidence=confidence,
            cited_sources=cited_pmids
        )
```

#### 2.3.2 Prompt Engineering

**System Prompts**:

```python
SYSTEM_PROMPTS = {
    'general_qa': """
You are an expert biomedical researcher with deep knowledge in molecular biology, genetics, and pharmacology. 
Your role is to help researchers understand complex scientific papers.

Guidelines:
- Be precise and factual
- Always cite sources with PMID
- Explain complex terms when needed
- Acknowledge limitations in the available data
""",
    
    'comparison': """
You are comparing multiple research papers. Highlight:
- Common findings
- Contradictory results
- Methodological differences
- Research gaps

Format your response with clear sections.
""",
    
    'trend_analysis': """
You are analyzing research trends over time. Focus on:
- Evolution of research questions
- Emerging methodologies
- Paradigm shifts
- Future directions

Provide data-driven insights.
"""
}
```

**Few-shot Examples**:

```python
FEW_SHOT_EXAMPLES = [
    {
        'question': "What are the side effects of CAR-T therapy?",
        'context': "[Paper 1] PMID: 12345678\nCAR-T therapy commonly causes cytokine release syndrome (CRS) in 60% of patients...",
        'answer': "According to recent research [PMID: 12345678], CAR-T therapy has several notable side effects:\n\n1. **Cytokine Release Syndrome (CRS)**: Occurs in approximately 60% of patients, characterized by fever, hypotension, and inflammatory responses...\n\nThe severity ranges from mild (Grade 1-2) to life-threatening (Grade 4-5)."
    }
]
```

#### 2.3.3 LLM API Integration

**OpenAI API**:
```python
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAIClient:
    
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = "gpt-4-turbo-preview"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_completion(
        self,
        messages: List[dict],
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> str:
        """
        GPT-4 호출
        
        Args:
            messages: [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."}
            ]
        """
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        return response.choices[0].message.content
    
    async def generate_with_function_call(
        self,
        messages: List[dict],
        functions: List[dict]
    ):
        """함수 호출 포함 (향후 도구 사용 확장)"""
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            functions=functions,
            function_call="auto"
        )
        
        return response
```

**Cost Optimization**:
```python
class CostOptimizer:
    
    def __init__(self):
        # Pricing (as of 2024.12)
        self.pricing = {
            'gpt-4': {'input': 0.03, 'output': 0.06},  # per 1K tokens
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}
        }
        
        # Response cache
        self.cache = Redis(host='localhost', port=6379)
    
    async def get_cached_or_generate(
        self,
        question: str,
        context: str
    ) -> str:
        """캐시 확인 후 LLM 호출"""
        # Create cache key
        cache_key = hashlib.md5(
            (question + context).encode()
        ).hexdigest()
        
        # Check cache
        cached_response = self.cache.get(cache_key)
        if cached_response:
            return cached_response.decode()
        
        # Generate
        response = await self.llm.generate(question, context)
        
        # Cache for 7 days
        self.cache.setex(cache_key, 604800, response)
        
        return response
```

---

### 2.4 Search & Recommendation Module

#### 2.4.1 Semantic Search

```python
class SemanticSearchService:
    
    async def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        의미 기반 논문 검색
        
        Args:
            query: 자연어 쿼리
            filters: 연도, 저널, 저자 등 필터
            top_k: 결과 수
        """
        
        # 1. Query expansion (동의어 포함)
        expanded_query = self._expand_query(query)
        
        # 2. Embed query
        query_embedding = self.embedding_gen.encode(expanded_query)
        
        # 3. Vector search
        vector_results = self.vector_store.search(
            query_embedding,
            top_k=top_k * 2
        )
        
        # 4. Apply metadata filters
        if filters:
            vector_results = self._apply_filters(vector_results, filters)
        
        # 5. Aggregate by paper (group chunks)
        paper_results = self._aggregate_chunks(vector_results)
        
        # 6. Rank papers
        ranked_papers = self._rank_papers(paper_results, query)
        
        return ranked_papers[:top_k]
    
    def _expand_query(self, query: str) -> str:
        """
        쿼리 확장 (동의어, 약어)
        
        Example: "T cell" → "T cell OR T lymphocyte OR T-cell"
        """
        # Load biomedical ontology
        synonyms = self.ontology.get_synonyms(query)
        
        expanded = query
        if synonyms:
            expanded = f"{query} OR {' OR '.join(synonyms)}"
        
        return expanded
```

#### 2.4.2 Recommendation System

**Collaborative Filtering + Content-Based**:

```python
class PaperRecommender:
    
    def recommend_similar_papers(
        self,
        paper_id: str,
        top_k: int = 5,
        method: str = 'hybrid'
    ) -> List[Paper]:
        """
        유사 논문 추천
        
        Methods:
        - 'content': 내용 기반 (embedding similarity)
        - 'citation': 인용 기반 (citation network)
        - 'hybrid': 혼합 (0.7 * content + 0.3 * citation)
        """
        
        if method == 'content':
            return self._content_based_recommendation(paper_id, top_k)
        elif method == 'citation':
            return self._citation_based_recommendation(paper_id, top_k)
        else:
            return self._hybrid_recommendation(paper_id, top_k)
    
    def _content_based_recommendation(
        self,
        paper_id: str,
        top_k: int
    ) -> List[Paper]:
        """코사인 유사도 기반"""
        # Get paper embedding (average of all chunks)
        paper_embedding = self._get_paper_embedding(paper_id)
        
        # Find similar papers
        similar_papers = self.vector_store.search(
            paper_embedding,
            top_k=top_k + 1  # +1 to exclude self
        )
        
        # Exclude the query paper itself
        similar_papers = [p for p in similar_papers if p['pmid'] != paper_id]
        
        return similar_papers[:top_k]
    
    def _citation_based_recommendation(
        self,
        paper_id: str,
        top_k: int
    ) -> List[Paper]:
        """인용 관계 기반 (co-citation analysis)"""
        # Get papers that cite this paper
        citing_papers = self.db.get_citing_papers(paper_id)
        
        # Get papers cited by this paper
        cited_papers = self.db.get_cited_papers(paper_id)
        
        # Co-citation: papers frequently cited together
        co_cited_scores = self._compute_co_citation_scores(
            cited_papers,
            all_papers
        )
        
        return sorted(co_cited_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    def _hybrid_recommendation(
        self,
        paper_id: str,
        top_k: int,
        content_weight: float = 0.7
    ) -> List[Paper]:
        """혼합 추천"""
        content_scores = self._content_based_recommendation(paper_id, top_k * 2)
        citation_scores = self._citation_based_recommendation(paper_id, top_k * 2)
        
        # Normalize scores
        content_scores_norm = self._normalize_scores(content_scores)
        citation_scores_norm = self._normalize_scores(citation_scores)
        
        # Combine scores
        hybrid_scores = {}
        for paper in set(content_scores.keys()) | set(citation_scores.keys()):
            hybrid_scores[paper] = (
                content_weight * content_scores_norm.get(paper, 0) +
                (1 - content_weight) * citation_scores_norm.get(paper, 0)
            )
        
        # Sort and return top-k
        return sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
```

---

### 2.5 Analytics & Trend Analysis Module

#### 2.5.1 Keyword Extraction

```python
from sklearn.feature_extraction.text import TfidfVectorizer
import yake

class KeywordExtractor:
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        # YAKE keyword extractor
        self.yake_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,  # n-grams up to 3
            dedupLim=0.9,
            top=20
        )
    
    def extract_keywords(
        self,
        documents: List[str],
        method: str = 'yake'
    ) -> List[tuple]:
        """
        키워드 추출
        
        Returns:
            [(keyword, score), ...]
        """
        if method == 'tfidf':
            return self._tfidf_extraction(documents)
        elif method == 'yake':
            return self._yake_extraction(documents)
        elif method == 'biobert':
            return self._biobert_extraction(documents)
    
    def _yake_extraction(self, text: str) -> List[tuple]:
        """YAKE 알고리즘"""
        keywords = self.yake_extractor.extract_keywords(text)
        return keywords
    
    def _biobert_extraction(self, text: str) -> List[str]:
        """BioBERT 기반 entity extraction"""
        from transformers import pipeline
        
        ner = pipeline(
            "ner",
            model="dmis-lab/biobert-base-cased-v1.1",
            aggregation_strategy="simple"
        )
        
        entities = ner(text)
        
        # Filter for GENE, PROTEIN, DISEASE entities
        bio_entities = [
            e['word'] for e in entities
            if e['entity_group'] in ['GENE', 'PROTEIN', 'DISEASE']
        ]
        
        return bio_entities
```

#### 2.5.2 Trend Analysis

```python
import pandas as pd
from datetime import datetime, timedelta

class TrendAnalyzer:
    
    def compute_keyword_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        keywords: Optional[List[str]] = None,
        aggregation: str = 'monthly'
    ) -> pd.DataFrame:
        """
        시계열 키워드 트렌드
        
        Returns:
            DataFrame with columns: [date, keyword, count]
        """
        
        # Query papers in date range
        papers = self.db.query_papers_by_date(start_date, end_date)
        
        # Extract keywords from each paper
        if keywords is None:
            keywords = self._extract_top_keywords(papers, top_n=50)
        
        # Count keyword occurrences over time
        trend_data = []
        
        date_range = self._get_date_range(start_date, end_date, aggregation)
        
        for date in date_range:
            papers_in_period = self._filter_papers_by_period(
                papers,
                date,
                aggregation
            )
            
            for keyword in keywords:
                count = self._count_keyword_occurrences(
                    papers_in_period,
                    keyword
                )
                
                trend_data.append({
                    'date': date,
                    'keyword': keyword,
                    'count': count
                })
        
        df = pd.DataFrame(trend_data)
        return df
    
    def detect_emerging_topics(
        self,
        window_months: int = 6,
        growth_threshold: float = 2.0
    ) -> List[str]:
        """
        급부상 토픽 탐지
        
        Args:
            window_months: 비교 기간 (개월)
            growth_threshold: 증가율 임계값 (2.0 = 200% 증가)
            
        Returns:
            List of emerging keywords
        """
        
        # Recent period
        end_date = datetime.now()
        start_date_recent = end_date - timedelta(days=window_months * 30)
        
        # Past period (for comparison)
        start_date_past = start_date_recent - timedelta(days=window_months * 30)
        end_date_past = start_date_recent
        
        # Get keyword counts
        recent_counts = self._get_keyword_counts(start_date_recent, end_date)
        past_counts = self._get_keyword_counts(start_date_past, end_date_past)
        
        # Compute growth rates
        emerging_keywords = []
        
        for keyword in recent_counts.keys():
            recent_count = recent_counts[keyword]
            past_count = past_counts.get(keyword, 1)  # Avoid division by zero
            
            growth_rate = recent_count / past_count
            
            if growth_rate >= growth_threshold and recent_count >= 10:
                emerging_keywords.append((keyword, growth_rate))
        
        # Sort by growth rate
        emerging_keywords.sort(key=lambda x: x[1], reverse=True)
        
        return [kw for kw, _ in emerging_keywords]
    
    def build_research_map(
        self,
        papers: List[Paper],
        min_citation_count: int = 5
    ) -> nx.Graph:
        """
        논문 관계 네트워크 생성
        
        Returns:
            NetworkX graph with nodes=papers, edges=citations/similarity
        """
        import networkx as nx
        
        G = nx.Graph()
        
        # Add nodes (papers)
        for paper in papers:
            if paper.citation_count >= min_citation_count:
                G.add_node(
                    paper.pmid,
                    title=paper.title,
                    year=paper.publication_date.year,
                    citations=paper.citation_count
                )
        
        # Add edges (citation relationships)
        for paper in papers:
            cited_papers = self.db.get_cited_papers(paper.pmid)
            
            for cited_pmid in cited_papers:
                if G.has_node(cited_pmid):
                    G.add_edge(
                        paper.pmid,
                        cited_pmid,
                        weight=1,
                        type='citation'
                    )
        
        # Add similarity edges
        for paper1 in papers:
            similar_papers = self.recommender.recommend_similar_papers(
                paper1.pmid,
                top_k=3
            )
            
            for similar_paper in similar_papers:
                if G.has_node(similar_paper['pmid']):
                    G.add_edge(
                        paper1.pmid,
                        similar_paper['pmid'],
                        weight=similar_paper['similarity'],
                        type='similarity'
                    )
        
        return G
```

#### 2.5.3 Visualization

```python
class TrendVisualizer:
    
    def plot_keyword_trend(self, df: pd.DataFrame) -> plotly.graph_objs.Figure:
        """시계열 라인 차트"""
        import plotly.express as px
        
        fig = px.line(
            df,
            x='date',
            y='count',
            color='keyword',
            title='Keyword Trends Over Time',
            labels={'count': 'Mentions', 'date': 'Date'}
        )
        
        return fig
    
    def plot_heatmap(self, df: pd.DataFrame) -> plotly.graph_objs.Figure:
        """연도 × 주제 히트맵"""
        import plotly.express as px
        
        # Pivot table
        heatmap_data = df.pivot(
            index='keyword',
            columns='year',
            values='count'
        )
        
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Year", y="Keyword", color="Count"),
            title="Research Topic Heatmap",
            color_continuous_scale='Viridis'
        )
        
        return fig
    
    def plot_wordcloud(self, keywords: List[tuple]) -> None:
        """워드클라우드"""
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        # Convert to dict
        word_freq = {word: score for word, score in keywords}
        
        # Generate wordcloud
        wc = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis'
        ).generate_from_frequencies(word_freq)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title('Top Keywords in Biomedical Research')
        plt.show()
    
    def plot_network(self, G: nx.Graph) -> None:
        """논문 관계 네트워크"""
        import plotly.graph_objects as go
        from networkx.algorithms import community
        
        # Community detection
        communities = community.greedy_modularity_communities(G)
        
        # Layout
        pos = nx.spring_layout(G, k=0.5, iterations=50)
        
        # Create plotly traces
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])
        
        node_trace = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Citations',
                    xanchor='left',
                    titleside='right'
                )
            )
        )
        
        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            
            # Node info
            node_info = G.nodes[node]
            node_trace['text'] += tuple([node_info['title'][:30]])
            node_trace['marker']['color'] += tuple([node_info['citations']])
        
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title='Research Paper Network',
            showlegend=False,
            hovermode='closest',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig
```

---

## 3. Database Design

### 3.1 Relational Schema (PostgreSQL)

```sql
-- Papers table
CREATE TABLE papers (
    pmid VARCHAR(20) PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    full_text TEXT,
    doi VARCHAR(100),
    journal VARCHAR(255),
    publication_date DATE,
    citation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_papers_date ON papers(publication_date);
CREATE INDEX idx_papers_journal ON papers(journal);

-- Authors table
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    affiliation TEXT,
    email VARCHAR(255)
);

-- Paper-Author relationship
CREATE TABLE paper_authors (
    paper_pmid VARCHAR(20) REFERENCES papers(pmid),
    author_id INTEGER REFERENCES authors(id),
    author_order INTEGER,  -- First author = 1
    PRIMARY KEY (paper_pmid, author_id)
);

-- Keywords/MeSH terms
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    term VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50)  -- 'mesh', 'author_keyword', etc.
);

CREATE TABLE paper_keywords (
    paper_pmid VARCHAR(20) REFERENCES papers(pmid),
    keyword_id INTEGER REFERENCES keywords(id),
    PRIMARY KEY (paper_pmid, keyword_id)
);

-- Paper chunks (for RAG)
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_pmid VARCHAR(20) REFERENCES papers(pmid),
    section VARCHAR(50),  -- 'abstract', 'introduction', etc.
    text TEXT NOT NULL,
    chunk_index INTEGER,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_paper ON chunks(paper_pmid);

-- Citations
CREATE TABLE citations (
    citing_pmid VARCHAR(20) REFERENCES papers(pmid),
    cited_pmid VARCHAR(20) REFERENCES papers(pmid),
    PRIMARY KEY (citing_pmid, cited_pmid)
);

-- User tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Saved papers
CREATE TABLE user_saved_papers (
    user_id UUID REFERENCES users(id),
    paper_pmid VARCHAR(20) REFERENCES papers(pmid),
    saved_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    PRIMARY KEY (user_id, paper_pmid)
);

-- User queries (for analytics)
CREATE TABLE query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),  -- 'search', 'rag', 'recommendation'
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_logs_user ON query_logs(user_id);
CREATE INDEX idx_query_logs_date ON query_logs(created_at);
```

### 3.2 Vector DB Schema (ChromaDB)

```python
# Collection structure
{
    "name": "biomedical_papers",
    "metadata": {
        "hnsw:space": "cosine",
        "description": "Embeddings for biomedical paper chunks"
    },
    "documents": [
        # Chunk text
    ],
    "embeddings": [
        # 768-dimensional vectors
    ],
    "metadatas": [
        {
            "pmid": "38123456",
            "title": "CAR-T cell therapy for...",
            "section": "abstract",
            "publication_date": "2024-03-15",
            "journal": "Nature Medicine",
            "chunk_id": "uuid-here",
            "token_count": 512
        }
    ],
    "ids": [
        # UUID for each chunk
    ]
}
```

---

## 4. API Design

### 4.1 REST API Endpoints

**Base URL**: `https://api.bio-rag.com/v1`

#### Authentication
```
POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/refresh-token
```

#### Search
```
GET  /search?q={query}&limit={limit}&filters={filters}
POST /search/advanced
```

**Request (POST)**:
```json
{
  "query": "CRISPR off-target effects",
  "filters": {
    "year_range": [2020, 2024],
    "journals": ["Nature", "Cell"],
    "sort_by": "relevance"
  },
  "limit": 10
}
```

**Response**:
```json
{
  "results": [
    {
      "pmid": "38123456",
      "title": "Minimizing off-target effects...",
      "abstract": "...",
      "relevance_score": 0.94,
      "publication_date": "2024-03-15",
      "journal": "Nature",
      "authors": ["Smith J", "Doe A"],
      "citation_count": 42
    }
  ],
  "total": 156,
  "page": 1,
  "query_time_ms": 234
}
```

#### RAG Chat
```
POST /chat/query
GET  /chat/history/{session_id}
DELETE /chat/history/{session_id}
```

**Request**:
```json
{
  "question": "What are the latest CAR-T therapy improvements?",
  "session_id": "optional-session-uuid",
  "max_sources": 5,
  "temperature": 0.1
}
```

**Response**:
```json
{
  "answer": "Recent advances in CAR-T therapy include...",
  "sources": [
    {
      "pmid": "38234567",
      "title": "...",
      "relevance": 0.92,
      "excerpt": "..."
    }
  ],
  "confidence": 0.88,
  "response_time_ms": 1834
}
```

#### Recommendations
```
GET /recommendations/similar/{pmid}?limit={limit}
GET /recommendations/trending?period={period}
```

#### Analytics
```
GET /analytics/trends/keywords?start_date={date}&end_date={date}
GET /analytics/topics/emerging
GET /analytics/network/{pmid}
```

### 4.2 WebSocket API (for Real-time Chat)

```python
from fastapi import WebSocket

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive question
            data = await websocket.receive_json()
            question = data['question']
            
            # Stream response
            async for chunk in rag_service.stream_response(question):
                await websocket.send_json({
                    'type': 'chunk',
                    'content': chunk
                })
            
            # Send completion
            await websocket.send_json({
                'type': 'complete',
                'sources': [...]
            })
    
    except WebSocketDisconnect:
        print("Client disconnected")
```

---

## 5. Performance Requirements

### 5.1 Latency Targets

| Operation | Target (p50) | Target (p95) | Target (p99) |
|-----------|--------------|--------------|--------------|
| Search | 200ms | 500ms | 1s |
| RAG Query | 1s | 2s | 5s |
| Recommendation | 100ms | 300ms | 500ms |
| Page Load | 500ms | 1s | 2s |

### 5.2 Throughput

- Concurrent users: 500
- Requests per second: 100 (peak 500)
- DB queries per second: 1,000

### 5.3 Scalability

**Horizontal Scaling**:
- Stateless API servers (auto-scale with load)
- Vector DB sharding (by publication year or topic)
- Read replicas for PostgreSQL

**Caching Strategy**:
```python
# Redis caching layers
cache_config = {
    'search_results': {
        'ttl': 3600,  # 1 hour
        'max_size': 10000
    },
    'rag_responses': {
        'ttl': 86400,  # 24 hours
        'max_size': 5000
    },
    'embeddings': {
        'ttl': 604800,  # 7 days
        'max_size': 50000
    }
}
```

**Load Balancing**:
- NGINX for reverse proxy
- Round-robin + least connections
- Health checks every 10s

---

## 6. Security Requirements

### 6.1 Authentication & Authorization

**JWT Implementation**:
```python
from jose import jwt
from passlib.context import CryptContext

class AuthService:
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = "HS256"
        self.access_token_expire = 30  # minutes
    
    def create_access_token(self, user_id: str) -> str:
        """JWT 토큰 생성"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return self.pwd_context.verify(plain_password, hashed_password)
```

**Role-Based Access Control (RBAC)**:
```python
class Role(Enum):
    GUEST = "guest"  # Limited access
    USER = "user"    # Full access
    ADMIN = "admin"  # Management access

# Permission matrix
PERMISSIONS = {
    Role.GUEST: ['search', 'view_paper'],
    Role.USER: ['search', 'view_paper', 'rag_query', 'save_paper'],
    Role.ADMIN: ['*']  # All permissions
}
```

### 6.2 Data Protection

**Encryption**:
- At rest: AES-256 for sensitive data
- In transit: TLS 1.3
- API keys: Stored in HashiCorp Vault

**PII Handling**:
```python
# Anonymize user data in logs
def anonymize_query_log(query: str, user_id: str) -> dict:
    return {
        'query_hash': hashlib.sha256(query.encode()).hexdigest(),
        'user_id_hash': hashlib.sha256(user_id.encode()).hexdigest(),
        'timestamp': datetime.utcnow()
    }
```

### 6.3 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Rate limits
RATE_LIMITS = {
    'search': "60/minute",
    'rag_query': "20/minute",  # Higher cost
    'api_general': "100/minute"
}

@app.get("/search")
@limiter.limit(RATE_LIMITS['search'])
async def search_papers(request: Request, query: str):
    ...
```

### 6.4 Input Validation

```python
from pydantic import BaseModel, Field, validator

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    limit: int = Field(10, ge=1, le=100)
    
    @validator('query')
    def sanitize_query(cls, v):
        # Prevent SQL injection, XSS
        v = v.replace(';', '').replace('<', '').replace('>', '')
        return v.strip()
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

class TestEmbeddingGenerator:
    
    @pytest.fixture
    def embedding_gen(self):
        return EmbeddingGenerator(model_name="test-model")
    
    def test_encode_returns_correct_shape(self, embedding_gen):
        text = "This is a test paper about CRISPR."
        embedding = embedding_gen.encode(text)
        
        assert embedding.shape == (768,)
        assert np.isfinite(embedding).all()
    
    def test_batch_encode(self, embedding_gen):
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = embedding_gen.batch_encode(texts)
        
        assert embeddings.shape == (3, 768)
```

### 7.2 Integration Tests

```python
class TestRAGPipeline:
    
    @pytest.mark.asyncio
    async def test_end_to_end_query(self):
        """전체 RAG 파이프라인 테스트"""
        # Setup
        rag_service = RAGService(...)
        question = "What are CRISPR off-target effects?"
        
        # Execute
        response = await rag_service.query(question)
        
        # Verify
        assert response.answer is not None
        assert len(response.sources) > 0
        assert response.confidence > 0.5
        assert all(s['pmid'] for s in response.sources)
```

### 7.3 Load Testing (Locust)

```python
from locust import HttpUser, task, between

class BioRAGUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def search_papers(self):
        """검색 부하 테스트"""
        self.client.get(
            "/search",
            params={"q": "cancer immunotherapy", "limit": 10}
        )
    
    @task(1)
    def rag_query(self):
        """RAG 쿼리 부하 테스트 (더 무거운 작업)"""
        self.client.post(
            "/chat/query",
            json={"question": "What is CAR-T therapy?"}
        )

# Run: locust -f load_test.py --host=http://localhost:8000
```

### 7.4 Quality Assurance

**RAG Quality Metrics**:
```python
class RAGEvaluator:
    
    def evaluate_retrieval_quality(
        self,
        test_cases: List[dict]
    ) -> dict:
        """
        검색 품질 평가
        
        Metrics:
        - Precision@K
        - Recall@K
        - MRR (Mean Reciprocal Rank)
        """
        precision_scores = []
        recall_scores = []
        mrr_scores = []
        
        for case in test_cases:
            query = case['query']
            ground_truth = set(case['relevant_pmids'])
            
            # Retrieve
            results = self.search_service.search(query, top_k=10)
            retrieved = set([r['pmid'] for r in results])
            
            # Calculate metrics
            tp = len(ground_truth & retrieved)
            precision = tp / len(retrieved) if retrieved else 0
            recall = tp / len(ground_truth) if ground_truth else 0
            
            # MRR
            for i, r in enumerate(results, 1):
                if r['pmid'] in ground_truth:
                    mrr_scores.append(1 / i)
                    break
            
            precision_scores.append(precision)
            recall_scores.append(recall)
        
        return {
            'precision@10': np.mean(precision_scores),
            'recall@10': np.mean(recall_scores),
            'mrr': np.mean(mrr_scores)
        }
    
    def evaluate_answer_quality(
        self,
        test_cases: List[dict]
    ) -> dict:
        """
        답변 품질 평가 (LLM-as-a-Judge)
        """
        from openai import OpenAI
        
        client = OpenAI()
        
        scores = []
        
        for case in test_cases:
            question = case['question']
            answer = self.rag_service.query(question).answer
            reference = case['reference_answer']
            
            # Use GPT-4 to judge answer quality
            judge_prompt = f"""
            Rate the quality of the AI answer compared to the reference answer.
            
            Question: {question}
            
            AI Answer: {answer}
            
            Reference Answer: {reference}
            
            Rate from 1-5:
            5 = Excellent (all key points covered, accurate)
            4 = Good (most key points, minor omissions)
            3 = Acceptable (some key points, some errors)
            2 = Poor (major omissions or errors)
            1 = Unacceptable (completely wrong or irrelevant)
            
            Provide rating (1-5) and brief justification.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": judge_prompt}]
            )
            
            # Parse rating
            rating = self._parse_rating(response.choices[0].message.content)
            scores.append(rating)
        
        return {
            'average_score': np.mean(scores),
            'scores': scores
        }
```

---

## 8. Monitoring & Observability

### 8.1 Metrics Collection

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Request counters
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

# Latency histogram
request_latency = Histogram(
    'request_latency_seconds',
    'Request latency',
    ['endpoint']
)

# Active users gauge
active_users = Gauge(
    'active_users',
    'Number of active users'
)

# LLM API costs
llm_api_cost = Counter(
    'llm_api_cost_usd',
    'Cumulative LLM API costs',
    ['model']
)
```

**Custom Metrics**:
```python
# Search quality
search_quality = Histogram(
    'search_relevance_score',
    'Search result relevance scores',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Cache hit rate
cache_hits = Counter('cache_hits_total', 'Cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Cache misses', ['cache_type'])
```

### 8.2 Logging

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

# Example usage
logger.info(
    "rag_query_completed",
    user_id=user_id,
    question_hash=question_hash,
    response_time_ms=response_time,
    sources_count=len(sources),
    confidence=confidence
)
```

**Log Levels**:
- DEBUG: Detailed execution flow
- INFO: General events (query, search)
- WARNING: Degraded performance, fallbacks
- ERROR: Failures, exceptions
- CRITICAL: System failures

### 8.3 Alerting

**Alert Rules** (Prometheus AlertManager):
```yaml
groups:
  - name: bio_rag_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(api_requests_total{status="500"}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
      
      - alert: SlowRAGQueries
        expr: histogram_quantile(0.95, request_latency_seconds{endpoint="/chat/query"}) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "RAG queries are slow (p95 > 5s)"
      
      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / rate(cache_requests_total[5m]) < 0.5
        for: 10m
        labels:
          severity: warning
```

### 8.4 Dashboards (Grafana)

**Dashboard Panels**:
1. Request Volume (line chart)
2. Latency Percentiles (p50, p95, p99)
3. Error Rate (%)
4. Active Users (gauge)
5. Top Search Queries (table)
6. LLM API Costs (stacked area)
7. Database Connection Pool (gauge)
8. Cache Hit Rate (%)

---

## 9. Deployment Architecture

### 9.1 Infrastructure (AWS)

```
┌──────────────────────────────────────────────────────┐
│                  Route 53 (DNS)                      │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│            CloudFront (CDN)                          │
│            - Static assets                           │
│            - API caching                             │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│         Application Load Balancer                    │
│         - SSL termination                            │
│         - Health checks                              │
└────┬─────────────────────────────────┬───────────────┘
     │                                 │
┌────▼─────────┐              ┌────────▼──────────┐
│   ECS/EKS    │              │   ECS/EKS        │
│   API Server │              │   Worker Nodes   │
│   (FastAPI)  │              │   (Celery)       │
└────┬─────────┘              └────────┬──────────┘
     │                                 │
┌────▼───────────────────────────────┬─▼───────────────┐
│         RDS PostgreSQL             │   ElastiCache   │
│         (Multi-AZ)                 │   (Redis)       │
└────────────────────────────────────┴─────────────────┘
```

**Compute**:
- ECS Fargate or EKS for container orchestration
- Auto-scaling: CPU > 70% or Request count
- Instance types: t3.medium (API), g4dn.xlarge (GPU for embeddings)

**Storage**:
- RDS PostgreSQL: db.r6g.large (Multi-AZ)
- S3: Paper PDFs, backups
- EFS: Shared model weights

**Networking**:
- VPC with public/private subnets
- NAT Gateway for outbound traffic
- Security Groups: Least privilege

### 9.2 CI/CD Pipeline

**GitHub Actions**:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml
      
      - name: Code quality (SonarQube)
        run: |
          sonar-scanner

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: |
          docker build -t bio-rag:${{ github.sha }} .
      
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login ...
          docker push bio-rag:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster bio-rag-cluster \
            --service bio-rag-api \
            --force-new-deployment
```

### 9.3 Disaster Recovery

**Backup Strategy**:
- Database: Daily automated backups, 7-day retention
- Vector DB: Weekly snapshots
- Application state: Immutable infrastructure

**RTO/RPO**:
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 1 hour

**Failover**:
- Multi-AZ deployment for RDS
- Cross-region replication for critical data
- Blue-Green deployment for zero-downtime

---

## 10. Cost Estimation

### 10.1 Infrastructure Costs (Monthly, USD)

| Service | Spec | Cost |
|---------|------|------|
| **Compute** | | |
| ECS Fargate (API) | 4 vCPU, 8GB RAM × 3 instances | $350 |
| ECS Fargate (Workers) | 2 vCPU, 4GB RAM × 2 instances | $150 |
| **Database** | | |
| RDS PostgreSQL | db.r6g.large Multi-AZ | $400 |
| ElastiCache Redis | cache.r6g.large | $250 |
| **Storage** | | |
| S3 (PDFs, backups) | 500 GB | $12 |
| EFS (model weights) | 50 GB | $15 |
| **Network** | | |
| CloudFront | 1 TB transfer | $85 |
| ALB | 1000 hrs + 10 GB processed | $30 |
| **Monitoring** | | |
| CloudWatch Logs | 50 GB ingestion | $25 |
| DataDog (optional) | 10 hosts | $150 |
| **Total (Infrastructure)** | | **~$1,467** |

### 10.2 API Costs (Monthly)

| API | Usage | Cost per 1K tokens | Monthly Cost |
|-----|-------|-------------------|--------------|
| OpenAI GPT-4 | 10M tokens (input) | $0.03 | $300 |
| | 5M tokens (output) | $0.06 | $300 |
| OpenAI Embeddings | 50M tokens | $0.0001 | $5 |
| **Total (API)** | | | **~$605** |

**Total Estimated Monthly Cost**: $1,467 + $605 = **~$2,072**

### 10.3 Cost Optimization Strategies

1. **Caching**: Reduce LLM API calls by 60%
2. **Reserved Instances**: Save 30% on RDS/ElastiCache
3. **Spot Instances**: For batch jobs, save 70%
4. **Compression**: Reduce S3 storage by 50%

**Optimized Monthly Cost**: ~$1,200

---

## 11. Development Timeline

### Week-by-Week Breakdown

| Week | Milestone | Tasks | Owner |
|------|-----------|-------|-------|
| **1** | Architecture & Setup | - System design<br>- ERD creation<br>- Git setup<br>- Dev environment | All |
| **2** | Data Collection | - PubMed API integration<br>- PDF processing<br>- Batch scheduler | Backend |
| **3** | Embedding & Vector DB | - Model selection & fine-tuning<br>- Chunking logic<br>- ChromaDB/FAISS setup | ML Engineer |
| **4** | RAG Implementation | - LangChain integration<br>- Prompt engineering<br>- Response validation | ML Engineer |
| **5** | Search & Recommendation | - Semantic search<br>- Similarity algorithm<br>- API endpoints | Backend |
| **6** | UI & Analytics | - React dashboard<br>- Trend charts<br>- Admin panel | Frontend |
| **7** | Testing & Deployment | - Load testing<br>- Security audit<br>- AWS deployment | DevOps |

---

## 12. Appendix

### 12.1 Glossary

- **Embedding**: Dense vector representation of text
- **RAG**: Retrieval-Augmented Generation
- **PMID**: PubMed Unique Identifier
- **MeSH**: Medical Subject Headings
- **Chunking**: Splitting text into smaller segments
- **Hallucination**: LLM generating false information

### 12.2 References

- [PubMed E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [LangChain Documentation](https://python.langchain.com/)
- [BioBERT Paper](https://arxiv.org/abs/1901.08746)
- [RAG Survey Paper](https://arxiv.org/abs/2312.10997)
- [ChromaDB Docs](https://docs.trychroma.com/)

### 12.3 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024.12 | Initial TRD |

---

**Document Approval**:
- Tech Lead: ___________
- ML Engineer: ___________
- DevOps Engineer: ___________
