import numpy as np
from typing import List
import arxiv
import logging

LOGGER = logging.getLogger(__name__)


def encode_paper(paper_id: str, encoder_model) -> np.ndarray:
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[paper_id])
        paper = next(client.results(search))
        
        text = f"{paper.title}. {paper.summary}"

        embedding = encoder_model.encode(text, convert_to_numpy=True)
        
        LOGGER.info(f"Successfully encoded paper {paper_id}")
        return embedding
        
    except Exception as e:
        LOGGER.error(f"Error encoding paper {paper_id}: {e}")
        raise


def encode_papers_batch(paper_ids: List[str], encoder_model) -> dict:
    embeddings = {}
    
    for paper_id in paper_ids:
        try:
            embeddings[paper_id] = encode_paper(paper_id, encoder_model)
        except Exception as e:
            LOGGER.warning(f"Skipping paper {paper_id} due to error: {e}")
            continue
            
    LOGGER.info(f"Successfully encoded {len(embeddings)} out of {len(paper_ids)} papers")
    return embeddings


def compare_vectors(vector1: np.ndarray, vector2: np.ndarray, method: str = "cosine") -> float:
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    # Check dimensions match
    if v1.shape != v2.shape:
        raise ValueError(f"Vector dimensions don't match: {v1.shape} vs {v2.shape}")

    if method == "cosine":
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
        
    elif method == "euclidean":
        distance = np.linalg.norm(v1 - v2)
        return float(distance)
        
    elif method == "dot":
        similarity = np.dot(v1, v2)
        return float(similarity)
        
    else:
        raise ValueError(f"Unknown comparison method: {method}. Use 'cosine', 'euclidean', or 'dot'")


def compare_papers(paper_id1: str, paper_id2: str, encoder_model, method: str = "cosine") -> float:
    embedding1 = encode_paper(paper_id1, encoder_model)
    embedding2 = encode_paper(paper_id2, encoder_model)
    
    similarity = compare_vectors(embedding1, embedding2, method=method)
    
    LOGGER.info(f"Similarity between {paper_id1} and {paper_id2} ({method}): {similarity:.4f}")
    return similarity


def find_similar_papers(target_paper_id: str, paper_embeddings: dict, 
                       encoder_model, top_k: int = 5, method: str = "cosine") -> List[tuple]:
    if target_paper_id in paper_embeddings:
        target_embedding = paper_embeddings[target_paper_id]
    else:
        target_embedding = encode_paper(target_paper_id, encoder_model)
    
    # Calculate similarities
    similarities = []
    for paper_id, embedding in paper_embeddings.items():
        if paper_id == target_paper_id:
            continue
            
        similarity = compare_vectors(target_embedding, embedding, method=method)
        similarities.append((paper_id, similarity))
    
    if method == "euclidean":
        similarities.sort(key=lambda x: x[1])
    else:
        similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_k]
