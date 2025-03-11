import requests
import pandas as pd
import typer
import logging
import xml.etree.ElementTree as ET
import re

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

app = typer.Typer()
logging.basicConfig(level=logging.INFO)


def fetch_paper_ids(query: str, max_results: int = 50):
    """Fetches paper IDs from PubMed based on a search query."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results
    }
    response = requests.get(PUBMED_SEARCH_URL, params=params)

    if response.status_code != 200:
        logging.error("Error fetching data from PubMed")
        return []

    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_paper_details(pubmed_id: str):
    """Fetches detailed paper information including publication date, authors, and affiliations."""
    params = {
        "db": "pubmed",
        "id": pubmed_id,
        "retmode": "xml"
    }

    response = requests.get(PUBMED_EFETCH_URL, params=params)

    if response.status_code != 200:
        logging.warning(f"Failed to fetch details for PubMed ID: {pubmed_id}")
        return {}

    root = ET.fromstring(response.text)

    # ✅ Extract Title
    title = root.find(".//ArticleTitle")
    title_text = title.text if title is not None else "Unknown Title"

    # ✅ Extract Publication Date
    pub_date = root.find(".//PubDate")
    if pub_date is not None:
        year = pub_date.find("Year").text if pub_date.find("Year") is not None else "Unknown"
        month = pub_date.find("Month").text if pub_date.find("Month") is not None else "Unknown"
        day = pub_date.find("Day").text if pub_date.find("Day") is not None else "Unknown"
        publication_date = f"{year}-{month}-{day}".replace("Unknown-", "").strip("-")
    else:
        publication_date = "Unknown Date"

    # ✅ Extract Non-Academic Authors & Company Affiliations
    non_academic_authors = []
    company_affiliations = []

    for author in root.findall(".//Author"):
        last_name = author.find("LastName")
        fore_name = author.find("ForeName")
        full_name = f"{fore_name.text} {last_name.text}" if fore_name is not None and last_name is not None else "Unknown Author"

        affiliation = author.find(".//Affiliation")
        if affiliation is not None:
            affiliation_text = affiliation.text.lower() if affiliation.text else ""
            if not is_academic(affiliation_text):  # Exclude academic affiliations
                non_academic_authors.append(full_name)
            if "ltd" in affiliation_text or "inc" in affiliation_text or "corp" in affiliation_text:
                company_affiliations.append(affiliation.text)

    # ✅ Extract Corresponding Author Email
    email = extract_corresponding_author_email(response.text)

    return {
        "PubmedID": pubmed_id,
        "Title": title_text,
        "Publication Date": publication_date,
        "Non-Academic Authors": ", ".join(non_academic_authors) if non_academic_authors else "None",
        "Company Affiliations": ", ".join(company_affiliations) if company_affiliations else "None",
        "Corresponding Author Email": email,
    }


def is_academic(affiliation: str) -> bool:
    """Checks if an affiliation is academic."""
    academic_keywords = ["university", "institute", "college", "school", "lab", "research", "faculty", "department"]
    return any(keyword in affiliation.lower() for keyword in academic_keywords)


def extract_corresponding_author_email(xml_data):
    """Extracts email addresses from XML using regex."""
    if not xml_data:
        return "Not Available"

    # Use regex to find email addresses in the XML data
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", xml_data)

    if emails:
        return emails[0]  # Return the first found email

    return "Not Available"


def process_papers(query: str, filename: str, debug: bool):
    """Fetches and processes papers, then saves to CSV."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"Fetching papers for query: {query}")
    paper_ids = fetch_paper_ids(query)

    results = []
    for paper_id in paper_ids:
        details = fetch_paper_details(paper_id)

        results.append({
            "PubmedID": details["PubmedID"],
            "Title": details["Title"],
            "Publication Date": details["Publication Date"],
            "Non-Academic Authors": details["Non-Academic Authors"],
            "Company Affiliations": details["Company Affiliations"],
            "Corresponding Author Email": details["Corresponding Author Email"]
        })

    df = pd.DataFrame(results)
    df.to_csv(filename, index=False)
    logging.info(f"Results saved to {filename}")


@app.command()
def get_papers(query: str, file: str = "pubmed_results.csv", debug: bool = False):
    """CLI command to fetch and save research papers."""
    process_papers(query, file, debug)


if __name__ == "__main__":
    app()
