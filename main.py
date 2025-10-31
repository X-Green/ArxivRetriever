import json
import sys
import arxiv
from datetime import datetime
import logging

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))


def getPaperIDList(time_range, category_list):
    start_year, end_year = time_range
    paper_ids = []

    # Build query string for categories
    category_query = " OR ".join([f"cat:{cat}" for cat in category_list])

    client = arxiv.Client(
        page_size=10,
        delay_seconds=3,
    )

    search = arxiv.Search(
        query=category_query,
        max_results=10000,  # Adjust as needed
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    # Filter results by time range
    try:
        index = 0
        for result in client.results(search):
            LOGGER.debug("(%d) %s | id=%s | published=%s | authors=%s | primary_cat=%s", index, result.title, result.entry_id.split('/')[-1], result.published.isoformat(), ", ".join(a.name for a in result.authors), getattr(result, "primary_category", "N/A"))
            paper_year = result.published.year
            if start_year <= paper_year <= end_year:
                paper_ids.append(result.entry_id.split('/')[-1])
            index += 1
            break

    except arxiv.ArxivError as e:
        LOGGER.error(f"Error fetching papers from arXiv: {e}")

    return paper_ids

def getEncoderModel():
    # Load the encoder model for embedding generation
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L12-v2')
    return model


if __name__ == "__main__":
    from process import encode_papers_batch, compare_vectors, find_similar_papers
    
    paper_id_list = []
    with open(r"paper_arxiv_lists\CVPR2022_paper_ids.json", "r") as f:
        paper_list = json.load(f)
    
    # "http://arxiv.org/abs/2008.11600"
    for k,v in paper_list.items():
        if v is not None and "arxiv.org" in v and "cnn" in k.lower():
            paper_id_list.append(v.split('/')[-1])
    print(paper_id_list)

    LOGGER.info(f"Found {len(paper_id_list)} papers")

    encoder_model = getEncoderModel()

    LOGGER.info("Encoding papers...")
    paper_table = encode_papers_batch(paper_id_list, encoder_model)
    LOGGER.info(f"Encoded {len(paper_table)} papers into vectors")
    
    if len(paper_table) >= 2:
        paper_ids = list(paper_table.keys())
        similarity = compare_vectors(
            paper_table[paper_ids[0]], 
            paper_table[paper_ids[1]], 
            method="cosine"
        )
        LOGGER.info(f"Cosine similarity between first two papers: {similarity:.4f}")
        
        # Find similar papers to the first one
        similar_papers = find_similar_papers(
            paper_ids[0], 
            paper_table, 
            encoder_model, 
            top_k=5
        )
        LOGGER.info(f"Top 5 similar papers to {paper_ids[0]}:")
        for paper_id, score in similar_papers:
            LOGGER.info(f"  {paper_id}: {score:.4f}")
    

