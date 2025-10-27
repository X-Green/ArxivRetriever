# ======================CONFIGS==========================
ALL_PAPER_CVPR2025 = "https://openaccess.thecvf.com/CVPR2025?day=all"
ALL_PAPER_CVPR2024 = "https://openaccess.thecvf.com/CVPR2024?day=all"
ALL_PAPER_CVPR2023 = "https://openaccess.thecvf.com/CVPR2023?day=all"
ALL_PAPER_CVPR2022 = "https://openaccess.thecvf.com/CVPR2022?day=all"

ALL_PAPER_ICCV2025 = "https://openaccess.thecvf.com/ICCV2025?day=all"
ALL_PAPER_ICCV2023 = "https://openaccess.thecvf.com/ICCV2023?day=all"
ALL_PAPER_ICCV2021 = "https://openaccess.thecvf.com/ICCV2021?day=all"

# ICLR NeurIPS AAAI ICML ECCV

OUTPUT_DIR = "paper_arxiv_lists"

target_conferences = {
    "CVPR2025": ALL_PAPER_CVPR2025,
    "CVPR2024": ALL_PAPER_CVPR2024,
    "CVPR2023": ALL_PAPER_CVPR2023,
    "CVPR2022": ALL_PAPER_CVPR2022,
    "ICCV2025": ALL_PAPER_ICCV2025,
    "ICCV2023": ALL_PAPER_ICCV2023,
    "ICCV2021": ALL_PAPER_ICCV2021,
}
# ===========================LOCATION=====================
"""
For openaccess, the links are within the same layer as the paper title, at //*[@id="content"]/dl/dd[x]
Where x is line index. If one line is dt with class="ptitle", then the following multiple dd may contain the links of this paper, until next dt.
Each dd may contain multiple links, we need to find the one with arXiv or PDF.
"""

# =========================================================

import os
import json
import requests
from bs4 import BeautifulSoup
import time
import logging
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


def output_path(conference_name):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    return os.path.join(OUTPUT_DIR, f"{conference_name}_paper_ids.json")

def extract_links_from_dd(dd_element):
    links = dd_element.find_all('a')
    arxiv_link = None
    pdf_link = None

    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True).lower()

        # Check for arXiv link
        if 'arxiv' in text or 'arxiv.org' in href:
            if href.startswith('http'):
                arxiv_link = href
            else:
                arxiv_link = 'https://openaccess.thecvf.com' + href
            # Convert pdf link to abs link if needed
            if 'pdf' in arxiv_link:
                arxiv_link = arxiv_link.replace('/pdf/', '/abs/').replace('.pdf', '')

        # Check for PDF link
        elif 'pdf' in text or href.endswith('.pdf'):
            if href.startswith('http'):
                pdf_link = href
            else:
                pdf_link = 'https://openaccess.thecvf.com' + href

    return arxiv_link, pdf_link

def fetch_papers(conference_url):
    """
    Fetch all papers from the conference page
    Returns a dict with paper titles as keys and links (arxiv or pdf) as values
    """
    logger.info(f"Fetching papers from {conference_url}")

    try:
        response = requests.get(conference_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch {conference_url}: {e}")
        return {}

    soup = BeautifulSoup(response.content, 'html.parser')
    papers = {}

    # Find the content section
    content = soup.find('div', id='content')
    if not content:
        logger.warning(f"Could not find content section in {conference_url}")
        return {}

    dl = content.find('dl')
    if not dl:
        logger.warning(f"Could not find dl element in {conference_url}")
        return {}

    current_title = "NULL"

    for line in dl.contents:
        # Extract paper title
        # pass
        if line.name == 'dt' and 'ptitle' in line.get('class', []):
            current_title = line.get_text(strip=True)
            logger.debug(f"Found paper title: {current_title}")

        elif line.name == 'dd':
            arxiv_link, pdf_link = extract_links_from_dd(line)
            papers[current_title] = arxiv_link if arxiv_link else pdf_link

    logger.info(f"Found {len(papers)} papers")
    return papers


def crawl_and_save(conference_name, conference_url):
    """
    Crawl a conference and save the results to JSON
    """
    logger.info(f"Processing {conference_name}...")
    papers = fetch_papers(conference_url)

    if papers:
        output_file = output_path(conference_name)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(papers)} papers to {output_file}")
    else:
        logger.warning(f"No papers found for {conference_name}")

    return papers


def main():
    """
    Main function to crawl all target conferences
    """
    logger.info("Starting conference paper crawler...")

    for conference_name, conference_url in target_conferences.items():
        try:
            crawl_and_save(conference_name, conference_url)
            # Be polite and wait between requests
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error processing {conference_name}: {e}")

    logger.info("Crawling completed!")


if __name__ == "__main__":
    main()
