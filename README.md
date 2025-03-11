PubMed Research Paper Fetcher - CLI Tool
=========================================

Overview:
---------
This tool allows users to fetch research papers from NCBI's PubMed database using a command-line interface (CLI).
It extracts key details including:

✅ Publication Date  
✅ Title  
✅ Non-Academic Authors  
✅ Company Affiliations  
✅ Corresponding Author Email  

All results are saved in a CSV file for easy access and analysis.

---

Installation & Setup:
---------------------
1️⃣ Install Poetry (if not installed):
   pip install poetry  

2️⃣ Clone this repository:
   git clone <your-repository-url>  
   cd pubmed_fetcher  

3️⃣ Install dependencies:
   poetry install  

---

Usage Instructions:
-------------------
Run the following command to fetch papers:  
   poetry run get-papers-list "<search_query>" --file <output_filename.csv> --debug  

Example:
   poetry run get-papers-list "cancer research" --file results.csv --debug  

To check the output CSV file:
   poetry run python -c "import pandas as pd; df = pd.read_csv('pubmed_results.csv'); print(df.head())"  

---

Expected Output Format:
-----------------------
The output CSV file (`pubmed_results.csv`) will contain:

PubmedID,Title,Publication Date,Non-Academic Authors,Company Affiliations,Corresponding Author Email  
40066659,Inhibition of HDAC4 in granulosa cells...,2025-Mar-11,"John Doe, Alice Smith","ABC Biotech, XYZ Research","johndoe@biotech.com"  
...  

---

Project Structure:
------------------
📂 pubmed_fetcher/  
 ├── fetcher.py            (Fetch & process PubMed data)  
 ├── main.py               (CLI command handling)  
 ├── update_pubmed_data.py (Updates data formatting)  
 ├── __init__.py           (Package initialization)  
 ├── poetry.lock           (Dependency lock file)  
 ├── pyproject.toml        (Poetry configuration)  
 ├── README.txt            (Project documentation)  

---

Notes:
------
- The script fetches **up to 50 papers** at a time.  
- The **PubMed API does not always provide emails**, so missing emails appear as `"Not Available"`.  
- **Academic affiliations** (e.g., universities) are excluded from `"Company Affiliations"`.  

---

Contact:
--------
For questions, contact **[Your Name]** at **your.email@example.com** 📩  

---
✅ **Now you can include this `README.txt` in your project for submission!** 🚀  
