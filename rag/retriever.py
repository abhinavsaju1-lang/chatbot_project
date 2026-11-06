import os
import re
import math
from collections import Counter
from config import Config

STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
    'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is',
    'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
    'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
}

def _tokenize(text):
    return [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()) if w not in STOPWORDS]

class LightweightBM25Retriever:
    """
    Ultra-lightweight BM25 retriever using pure Python standard library.
    Zero PyTorch dependency, zero startup overhead, < 1MB RAM footprint.
    Perfect for Render 512MB RAM free tier.
    """
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or Config.DATA_DIR
        self.documents = []
        self.doc_tokens = []
        self.doc_lens = []
        self.avg_dl = 0
        self.idf = {}
        self.k1 = 1.5
        self.b = 0.75
        self._is_indexed = False

    def _ensure_indexed(self):
        if self._is_indexed:
            return

        if not os.path.exists(self.data_dir):
            return

        raw_chunks = []
        for filename in sorted(os.listdir(self.data_dir)):
            if filename.endswith(".txt"):
                path = os.path.join(self.data_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Split into natural section/topic paragraphs
                    paras = [p.strip() for p in re.split(r'\n\s*\n', content) if len(p.strip()) > 40]
                    raw_chunks.extend(paras)
                except Exception as e:
                    print(f"[RAG Warning] Failed reading {filename}: {e}")

        if not raw_chunks:
            raw_chunks = [
                "MindSense Mental Health Reference: Active listening, stress management, grounding exercises, and cognitive reframing.",
                "Coping Strategies: 5-minute breathing techniques, progressive muscle relaxation, structured sleep schedules, and exercise."
            ]

        self.documents = raw_chunks
        self.doc_tokens = [_tokenize(doc) for doc in self.documents]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avg_dl = sum(self.doc_lens) / max(len(self.doc_lens), 1)

        # Calculate IDF
        num_docs = len(self.documents)
        df = Counter()
        for tokens in self.doc_tokens:
            for term in set(tokens):
                df[term] += 1

        self.idf = {
            term: math.log(1 + (num_docs - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }
        self._is_indexed = True

    def retrieve(self, query, top_k=3):
        self._ensure_indexed()
        if not self.documents:
            return ""

        query_terms = _tokenize(query)
        if not query_terms:
            return self.documents[0] if self.documents else ""

        scores = []
        for idx, tokens in enumerate(self.doc_tokens):
            if not tokens:
                scores.append(0.0)
                continue

            tf = Counter(tokens)
            doc_len = self.doc_lens[idx]
            score = 0.0

            for term in query_terms:
                if term in tf:
                    term_freq = tf[term]
                    term_idf = self.idf.get(term, 0.5)
                    numerator = term_freq * (self.k1 + 1)
                    denominator = term_freq + self.k1 * (1 - self.b + self.b * (doc_len / max(self.avg_dl, 1)))
                    score += term_idf * (numerator / max(denominator, 0.001))

            scores.append((score, self.documents[idx]))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_matches = [doc for score, doc in scores[:top_k] if score > 0]
        
        # If no strict keyword overlap, return the primary guidelines chunk as safe fallback
        if not top_matches and self.documents:
            top_matches = [self.documents[0]]

        return "\n\n".join(top_matches)


class HybridRetriever:
    """
    Smart hybrid retriever that defaults to ultra-low-memory BM25,
    with optional FAISS vector search only when explicitly requested.
    """
    def __init__(self):
        self.light_retriever = LightweightBM25Retriever()
        self.vectorstore = None

    def retrieve_context(self, query, top_k=3):
        # 1. Check if FAISS is explicitly requested and configured
        use_faiss = os.getenv("USE_FAISS", "false").lower() in ("true", "1")
        if use_faiss:
            try:
                if self.vectorstore is None:
                    from rag.vectorstore import get_or_create_vectorstore
                    self.vectorstore = get_or_create_vectorstore()

                if self.vectorstore is not None:
                    docs = self.vectorstore.similarity_search(query, k=top_k)
                    if docs:
                        return "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                print(f"[FAISS Warning] FAISS retrieval failed, falling back to lightweight RAG: {e}")

        # 2. Ultra-lightweight BM25 retriever (0 extra RAM, instant execution)
        try:
            return self.light_retriever.retrieve(query, top_k=top_k)
        except Exception as e:
            print(f"[RAG Retriever Error] {e}")
            return ""


# Global singleton instance
_retriever = HybridRetriever()

def get_relevant_context(query):
    return _retriever.retrieve_context(query)
