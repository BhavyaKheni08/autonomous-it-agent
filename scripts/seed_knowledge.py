import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from app.core.config import settings

def load_documents(directory_path: str):
    """
    Scans the directory for PDF and TXT files and loads them.
    Using explicit globbing to handle different file types better than DirectoryLoader sometimes.
    """
    documents = []
    
    # Load TXT
    txt_files = glob.glob(os.path.join(directory_path, "**/*.txt"), recursive=True)
    for file_path in txt_files:
        try:
            loader = TextLoader(file_path)
            documents.extend(loader.load())
            print(f"Loaded: {file_path}")
        except Exception as e:
            print(f"Failed to load {file_path}: {e}")

    # Load PDF
    pdf_files = glob.glob(os.path.join(directory_path, "**/*.pdf"), recursive=True)
    for file_path in pdf_files:
        try:
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
            print(f"Loaded: {file_path}")
        except Exception as e:
            print(f"Failed to load {file_path}: {e}")
            
    return documents

def seed_knowledge_base():
    """
    Main function to ingest documents into ChromaDB.
    """
    source_dir = "data/source_docs"
    
    # 1. Setup Data Directory
    if not os.path.exists(source_dir):
        os.makedirs(source_dir)
        # Create dummy policy if empty
        dummy_file = os.path.join(source_dir, "policy.txt")
        if not os.path.exists(dummy_file):
            print("creating dummy policy.txt...")
            with open(dummy_file, "w") as f:
                f.write("IT Security Policy 2025: All passwords must be 16 characters long. use the portal at vpn.example.com.")
    
    # 2. Load
    docs = load_documents(source_dir)
    if not docs:
        print("No documents found.")
        return

    # 3. Split
    # selected chunk_size=1000 to keep enough context for the LLM to understand the policy.
    # overlap=200 ensures continuity between chunks if sentences are cut off.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)
    print(f"Total splits created: {len(splits)}")

    # 4. Embed & Store
    print(f"Embedding using model: {settings.OLLAMA_EMBEDDING_MODEL}")
    embedding_function = OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_EMBEDDING_MODEL
    )
    
    # Persist to Chroma
    # We use the standard langchain_chroma wrapper
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_function,
        collection_name="tech_docs",
        persist_directory=settings.CHROMA_DB_PATH
    )
    
    # Note: In newer langchain_chroma versions, persistence is automatic.
    print(f"Successfully ingested {len(splits)} chunks into ChromaDB at {settings.CHROMA_DB_PATH}.")

if __name__ == "__main__":
    seed_knowledge_base()
