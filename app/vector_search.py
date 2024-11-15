from typing import List, Dict, Optional
from langchain.schema import Document
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

if not openai_api_key:
    raise ValueError("OpenAI API key not found in environment variables")


def load_vectordb(load_path: str, model: str = "text-embedding-3-small") -> FAISS:
    """
    Load FAISS vector database from disk using OpenAI embeddings.
    
    Args:
        load_path: Path where the database is stored
        model: OpenAI embedding model name
    
    Returns:
        FAISS vector store object
    """
    try:
        # Initialize OpenAI embedding model
        embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model=model
        )
        
        # Load vector store
        vectorstore = FAISS.load_local(
            folder_path=load_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        return vectorstore
    except Exception as e:
        print(f"Error loading vector database: {str(e)}")
        return None


def search_similar_chunks(vectorstore: FAISS,
                         query: str,
                         k: int = 5,
                         filter_dict: Optional[Dict] = None) -> List[Document]:
    """
    Search for similar chunks in the vector database.
    
    Args:
        vectorstore: FAISS vector store
        query: Search query string
        k: Number of similar chunks to return
        filter_dict: Optional metadata filters
    
    Returns:
        List of similar Document objects
    """
    try:
        if filter_dict:
            similar_docs = vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            similar_docs = vectorstore.similarity_search(
                query,
                k=k
            )
        return similar_docs
    
    except Exception as e:
        print(f"Error during similarity search: {str(e)}")
        return []


def format_chunk_results(documents: List[Document],
                         metadata_fields: Optional[List[str]] = None,
                         include_content: bool = True,
                         max_content_length: Optional[int] = None) -> str:
    """
    Format search results into a readable string.
    
    Args:
        documents: List of Document objects from search results
        metadata_fields: List of metadata fields to include (None for all fields)
        include_content: Whether to include the content in output
        max_content_length: Maximum length of content to display (None for full content)
    
    Returns:
        Formatted string of search results
    """
    if not documents:
        return "No results found."
    
    # Default metadata fields if none specified
    default_fields = [
        'page_type',
        'primary_category',
        'subcategory',
        'title',
        'chunk_index',
        'total_chunks',
        'source'
    ]
    metadata_fields = metadata_fields or default_fields
    
    output_parts = []
    output_parts.append(f"Found {len(documents)} relevant chunks:\n")
    
    for i, doc in enumerate(documents, 1):
        # Add chunk header
        output_parts.append(f"\nChunk {i}:")
        output_parts.append("-" * 10)
        
        # Add metadata
        metadata_lines = []
        for field in metadata_fields:
            if field in doc.metadata:
                value = doc.metadata[field]
                # Format the field name for display
                display_field = field.replace('_', ' ').title()
                metadata_lines.append(f"{display_field}: {value}")
        output_parts.append('\n'.join(metadata_lines))
        
        # Add content if requested
        if include_content:
            output_parts.append("\nContent:")
            output_parts.append("-" * 10)
            content = doc.page_content
            if max_content_length and len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            output_parts.append(content)
            output_parts.append("-" * 10)
    
    return '\n'.join(output_parts)


def inspect_metadata(vectorstore: FAISS, sample_query: str = "sample", sample_size: int = 100) -> Dict[str, set]:
    """
    Inspect metadata fields and their potential values from a sample of documents.
    
    Args:
        vectorstore: FAISS vector store
        sample_query: A query string to use for fetching sample documents
        sample_size: Number of documents to sample for metadata inspection
    
    Returns:
        Dictionary with metadata fields as keys and sets of their unique values
    """
    metadata_summary = {}

    # Retrieve a sample of documents using a simple query
    sample_docs = vectorstore.similarity_search(query=sample_query, k=sample_size)

    for doc in sample_docs:
        for key, value in doc.metadata.items():
            if key not in metadata_summary:
                metadata_summary[key] = set()
            metadata_summary[key].add(value)
    
    return metadata_summary


if __name__ == "__main__":
    # Load the vector database
    base_dir = os.path.dirname(__file__)
    vectordb_path = os.path.join(base_dir, 'data', 'vectordb')
    db = load_vectordb(vectordb_path)
    
    if db:
        # Example searches with different queries
        test_queries = [
            "What are the core courses in the MS in Applied Data Science program?",
            "What are the admission requirements for the MS in Applied Data Science program?",
            "Can you provide information about the capstone project?"
        ]
        
        
        # Try each query
        for query in test_queries:
            print(f"\n\nQUERY: {query}")
            print("-"*50)
            
            # Search without filter
            chunks = search_similar_chunks(
                vectorstore=db,
                query=query,
                k=5
                # filter_dict={"primary_category": "example"}
            )

            chunks_formated = format_chunk_results(
            chunks,
            metadata_fields = [
                'page_type',
                'primary_category',
                'subcategory',
                'title',
                'source'
            ],
            include_content=True
            )

            print(chunks_formated)

            # Check metadata
            metadata_summary = inspect_metadata(db, sample_query="example", sample_size=500)
            print("Metadata Fields and Potential Values:")
            for field, values in metadata_summary.items():
                print(f"\n{field}:")
                for val in values:
                    print(f"  - {val}")