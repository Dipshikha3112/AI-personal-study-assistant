import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import pickle

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def scrape_study_materials(topics, num_results=5):
    """Scrape study materials and interview questions for given topics."""
    documents = []
    for topic in topics:
        query = f"{topic} study material | interview questions 2025 site:*.edu | site:glassdoor.com | site:geeksforgeeks.org"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            for url in search(query, num_results=num_results):
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    soup = BeautifulSoup(response.text, "html.parser")
                    paragraphs = soup.find_all("p")
                    text = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if text:
                        documents.append(text[:1000])  # Limit to 1000 chars per document
                except Exception as e:
                    print(f"Error fetching {url}: {e}")
        except Exception as e:
            print(f"Search error for {topic}: {e}")
    return list(set(documents))  # Remove duplicates

def build_faiss_index(documents, index_path="data/faiss_index", docs_path="data/documents.pkl"):
    """Build and save FAISS index from documents."""
    if not documents:
        print("No documents to index.")
        return None, None
    
    # Generate embeddings
    embeddings = embedding_model.encode(documents, show_progress_bar=True)
    
    # Create FAISS index
    dimension = embeddings.shape[1]  # Embedding dimension (384 for MiniLM)
    index = faiss.IndexFlatL2(dimension)  # L2 distance for similarity search
    index.add(np.array(embeddings, dtype=np.float32))
    
    # Save index and documents
    os.makedirs("data", exist_ok=True)
    faiss.write_index(index, index_path)
    with open(docs_path, "wb") as f:
        pickle.dump(documents, f)
    
    return index, documents

def main():
    # Define topics to scrape (customize based on your needs)
    topics = [
        "Python programming",
        "Data structures and algorithms",
        "Machine learning basics",
        "Software engineering interview questions",
        "System design concepts"
    ]
    
    # Scrape documents
    print("Scraping study materials...")
    documents = scrape_study_materials(topics, num_results=5)
    print(f"Collected {len(documents)} unique documents.")
    
    # Build and save FAISS index
    print("Building FAISS index...")
    index, documents = build_faiss_index(documents)
    if index:
        print(f"FAISS index saved at data/faiss_index with {len(documents)} documents.")

if __name__ == "__main__":
    main()
