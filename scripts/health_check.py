
import asyncio
import os
import sys
import requests
import chromadb
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def print_status(component, success, message=""):
    symbol = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
    print(f"{symbol} {component}: {message}")

async def check_postgres():
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print_status("PostgreSQL", True, "Connection successful")
        await engine.dispose()
        return True
    except Exception as e:
        print_status("PostgreSQL", False, f"Failed: {str(e)}")
        return False

def check_ollama():
    try:
        url = f"{settings.OLLAMA_BASE_URL}/api/tags"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json().get('models', [])]
            print_status("Ollama", True, f"Online (Models: {', '.join(models[:3])}...)")
            return True
        else:
            print_status("Ollama", False, f"Status Code: {resp.status_code}")
            return False
    except Exception as e:
        print_status("Ollama", False, f"Unreachable: {str(e)}")
        return False

def check_chroma():
    try:
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        try:
            coll = client.get_collection("tech_docs")
            count = coll.count()
            print_status("ChromaDB", True, f"Collection 'tech_docs' has {count} documents")
            return True
        except Exception:
            print_status("ChromaDB", False, "Collection 'tech_docs' not found")
            return False
    except Exception as e:
        print_status("ChromaDB", False, f"Failed to load: {str(e)}")
        return False

def check_api():
    url = "http://localhost:8000/docs"
    try:
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            print_status("FastAPI Backend", True, "Running at http://localhost:8000")
            return True
        else:
            print_status("FastAPI Backend", False, f"Returned {resp.status_code}")
            return False
    except Exception as e:
        print_status("FastAPI Backend", False, f"Connection failed: {str(e)}")
        return False

async def main():
    print("🏥 Starting System Health Check...\n")
    
    results = [
        await check_postgres(),
        check_ollama(),
        check_chroma(),
        check_api()
    ]
    
    print("\n------------------------------------------------")
    if all(results):
        print(f"{GREEN}All systems operational!{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}Some systems are down.{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
