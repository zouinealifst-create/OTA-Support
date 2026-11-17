import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# ── Config ─────────────────────────────────────────────────
GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY         = os.getenv("GROQ_API_KEY")
GROQ_MODEL           = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE     = float(os.getenv("GROQ_TEMPERATURE", 0.3))
GROQ_MAX_TOKENS      = int(os.getenv("GROQ_MAX_TOKENS", 1024))  # FIX: was defined in .env but unused
PINECONE_API_KEY     = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME")
PINECONE_REGION      = os.getenv("PINECONE_REGION", "us-east-1")
EMBEDDING_MODEL      = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", 768))  # FIX: was hardcoded to 768, now reads from env
DOCS_PATH            = os.getenv("DOCS_PATH", "knowledge_base/documents")
CHUNK_SIZE           = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP        = int(os.getenv("CHUNK_OVERLAP", 50))


# ── Pinecone connection ────────────────────────────────────
def get_pinecone_index():
    pc       = Pinecone(api_key=PINECONE_API_KEY)
    existing = [i.name for i in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing:
        print(f"Creating index: {PINECONE_INDEX_NAME}")
        pc.create_index(
            name      = PINECONE_INDEX_NAME,
            dimension = EMBEDDING_DIMENSIONS,  # FIX: now uses env value instead of hardcoded 768
            metric    = "cosine",
            spec      = ServerlessSpec(cloud="aws", region=PINECONE_REGION)
        )
        print("✓ Index created")
    else:
        print(f"✓ Index '{PINECONE_INDEX_NAME}' already exists")

    return pc.Index(PINECONE_INDEX_NAME)


# ── Gemini embeddings (Groq has no embeddings) ─────────────
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model          = EMBEDDING_MODEL,
        google_api_key = GEMINI_API_KEY
    )


# ── Groq LLM ──────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        api_key     = GROQ_API_KEY,
        model_name  = GROQ_MODEL,
        temperature = GROQ_TEMPERATURE,
        max_tokens  = GROQ_MAX_TOKENS  # FIX: was defined in .env but never passed
    )


# ── Load and split documents ───────────────────────────────
def load_documents():
    print(f"Loading documents from: {DOCS_PATH}")
    loader = DirectoryLoader(
        DOCS_PATH,
        glob          = "**/*.txt",
        loader_cls    = TextLoader,
        loader_kwargs = {"encoding": "utf-8"}
    )
    docs   = loader.load()
    print(f"✓ Loaded {len(docs)} document(s)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)
    print(f"✓ Split into {len(chunks)} chunks")
    return chunks


# ── Upload documents to Pinecone ───────────────────────────
def upload_documents():
    chunks     = load_documents()
    embeddings = get_embeddings()

    print("Uploading to Pinecone...")
    PineconeVectorStore.from_documents(
        documents  = chunks,
        embedding  = embeddings,
        index_name = PINECONE_INDEX_NAME
    )
    print(f"✓ {len(chunks)} chunks uploaded to Pinecone")


# ── Get retriever ──────────────────────────────────────────
def get_retriever():
    embeddings   = get_embeddings()
    vector_store = PineconeVectorStore(
        index_name = PINECONE_INDEX_NAME,
        embedding  = embeddings
    )
    return vector_store.as_retriever(
        search_type   = "similarity",
        search_kwargs = {"k": 3}
    )


# ── Answer a question via RAG ──────────────────────────────
def ask_knowledge_base(question: str) -> str:
    retriever = get_retriever()
    llm       = get_llm()

    prompt = ChatPromptTemplate.from_template("""
    You are a helpful customer support assistant.
    Use the following context to answer the question.
    If you don't know the answer, say so honestly.

    Context:
    {context}

    Question: {question}
    """)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(question)


# ── Run directly to upload docs ────────────────────────────
if __name__ == "__main__":
    print("\n── AntiGravity KB Setup ──────────────────")
    get_pinecone_index()
    upload_documents()
    print("── Done ──────────────────────────────────\n")