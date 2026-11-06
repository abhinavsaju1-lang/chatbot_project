from rag.vectorstore import get_or_create_vectorstore

class ContextRetriever:
    def __init__(self):
        self.vectorstore = None
        try:
            self.vectorstore = get_or_create_vectorstore()
        except Exception as e:
            print(f"[ContextRetriever Init Warning] FAISS Vectorstore not initialized at boot: {e}")

    def retrieve_context(self, query, top_k=3):
        """Retrieve top_k relevant context documents for a user query."""
        if self.vectorstore is None:
            try:
                self.vectorstore = get_or_create_vectorstore()
            except Exception:
                return ""

        if self.vectorstore is None:
            return ""

        try:
            docs = self.vectorstore.similarity_search(query, k=top_k)
            context_text = "\n\n".join([doc.page_content for doc in docs])
            return context_text
        except Exception as e:
            print(f"[Retriever Error] Similarity search failed: {e}")
            return ""

retriever_instance = ContextRetriever()

def get_relevant_context(query):
    return retriever_instance.retrieve_context(query)
