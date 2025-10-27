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

    except arxiv.ArxivError as e:
        LOGGER.error(f"Error fetching papers from arXiv: {e}")

    return paper_ids

def getEncoderModel():
    # Load the encoder model for embedding generation
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('Qwen3-Embedding-0.6B')
    return model


if __name__ == "__main__":
    paper_id_list = getPaperIDList(time_range = (2023, 2025), category_list= ("cs.AI", "cs.CV") )
    encoder_model = getEncoderModel()
    paper_table = dict()

    import code
    code.interact(local=locals())
