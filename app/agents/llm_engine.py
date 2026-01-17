from typing import Type, Any
from langchain_community.chat_models import ChatOllama
from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.core.config import settings

def get_llm():
    """
    Returns the standard ChatOllama instance.
    """
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0
    )

def get_structured_llm(pydantic_object: Type[BaseModel]) -> Any:
    """
    Returns a chain that enforces the Output format based on a Pydantic model.
    """
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=pydantic_object)
    
    # Simple formatting instructions
    format_instructions = parser.get_format_instructions()
    
    return llm, parser, format_instructions
