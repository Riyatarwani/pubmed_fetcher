import pandas as pd
import requests
import xml.etree.ElementTree as ET
import time
import re
import typer
from typing import Optional

PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def fetch_pubmed_data(pubmed_id):
    """Fetch detailed data for a PubMed ID using the NCBI E-utilities API"""
    params = {
        'db': 'pubmed', 
        'id': pubmed_id, 
        'retmode': 'xml',
        'rettype': 'abstract'
    }
    
    try:
        response = requests.get(PUBMED_EFETCH_URL, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching PubMed ID {pubmed_id}: Status code {response.status_code}")
            return None
        
        root = ET.fromstring(response.text)
        
        # Find the article
        article = root.find(".//PubmedArticle")
        if article is None:
            print(f"No article data found for PubMed ID {pubmed_id}")
            return None
        
        # Extract title
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None and title_elem.text else "Not Available"
        
        # Extract publication date
        pub_date = article.find(".//PubDate")
        if pub_date is not None:
            year = pub_date.find("Year")
            month = pub_date.find("Month")
            day = pub_date.find("Day")
            
            pub_date_str = []
            if year is not None and year.text:
                pub_date_str.append(year.text)
            if month is not None and month.text:
                pub_date_str.append(month.text)
            if day is not None and day.text:
                pub_date_str.append(day.text)
            
            publication_date = "-".join(pub_date_str) if pub_date_str else "Not Available"
        else:
            publication_date = "Not Available"
        
        # Extract authors and their affiliations
        author_list = article.findall(".//Author")
        non_academic_authors = []
        company_affiliations = []
        corresponding_email = "Not Available"
        
        # Process all authors
        for author in author_list:
            # Get author name
            lastname = author.find("LastName")
            firstname = author.find("ForeName") or author.find("FirstName")
            
            if lastname is not None and lastname.text:
                if firstname is not None and firstname.text:
                    author_name = f"{lastname.text}, {firstname.text}"
                else:
                    author_name = lastname.text
            else:
                collective_name = author.find("CollectiveName")
                if collective_name is not None and collective_name.text:
                    author_name = collective_name.text
                else:
                    continue
            
            # Process affiliations
            is_non_academic = False
            is_company = False
            
            # Check if author has affiliation info
            affiliations = []
            affil_elements = author.findall(".//Affiliation")
            
            if affil_elements:
                for affil in affil_elements:
                    if affil.text:
                        affiliations.append(affil.text)
                
                for affil_text in affiliations:
                    affil_lower = affil_text.lower()
                    
                    # Check for company affiliations
                    company_keywords = ["inc", "ltd", "llc", "corp", "company", "pharma", 
                                      "technologies", "biotech", "co.", "medical technology"]
                    if any(keyword in affil_lower for keyword in company_keywords):
                        is_company = True
                    
                    # Check for non-academic affiliations
                    academic_keywords = ["university", "institute", "college", "school", 
                                      "hospital", "clinic", "center for", "laboratory", 
                                      "medical center", "department of"]
                    if all(keyword not in affil_lower for keyword in academic_keywords):
                        is_non_academic = True
                    
                    # Look for emails if we haven't found a corresponding author yet
                    if corresponding_email == "Not Available":
                        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', affil_text)
                        if email_match:
                            corresponding_email = email_match.group(0)
            
            # Add author to appropriate lists
            if is_company:
                company_affiliations.append(author_name)
            if is_non_academic:
                non_academic_authors.append(author_name)
        
        # Use empty strings instead of None to avoid NaN in CSV
        return {
            "PubmedID": pubmed_id,
            "Title": title,
            "Publication Date": publication_date,
            "Non-Academic Authors": ", ".join(non_academic_authors) if non_academic_authors else "",
            "Company Affiliations": ", ".join(company_affiliations) if company_affiliations else "",
            "Corresponding Author Email": corresponding_email
        }
        
    except Exception as e:
        print(f"Error processing PubMed ID {pubmed_id}: {str(e)}")
        return None

def fix_current_data(input_file, output_file=None):
    """Fix formatting issues in current data file"""
    try:
        # Load the input file
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} records from {input_file}")
        
        # Replace NaN values with empty strings
        df = df.fillna("")
        
        # Ensure column names match expected format
        column_mapping = {
            "Non-academic Author(s)": "Non-Academic Authors",
            "Non-academic Authors": "Non-Academic Authors",
            "Company Affiliation(s)": "Company Affiliations"
        }
        
        df = df.rename(columns={col: column_mapping.get(col, col) for col in df.columns})
        
        # Save if output file is specified
        if output_file:
            df.to_csv(output_file, index=False)
            print(f"Fixed data saved to {output_file}")
        
        return df
    
    except Exception as e:
        print(f"Error fixing data: {str(e)}")
        raise

def main():
    """Main function to process PubMed data"""
    try:
        # Define file paths
        input_file = "fixed_pubmed_results.csv"  # Use the fixed CSV file
        output_file = "updated_pubmed_results.csv"  # Where to save updated data
        
        # Fix current data
        print(f"Fixing formatting in {input_file}...")
        df = fix_current_data(input_file)
        print("Current data sample:")
        print(df.head())
        
        # Ask if user wants to update with NCBI API
        update_choice = input("\nDo you want to fetch updated data from NCBI API? (y/n): ")
        
        if update_choice.lower() == 'y':
            # Ask how many records to process (for testing or to avoid rate limits)
            try:
                limit_input = input("How many records to process? (Enter for all): ")
                limit = int(limit_input) if limit_input.strip() else None
            except ValueError:
                limit = None
            
            # Fetch additional details
            updated_data = []
            total = len(df) if limit is None else min(limit, len(df))
            
            for i, row in df.head(total).iterrows():
                pubmed_id = str(row["PubmedID"])
                print(f"Processing {i+1}/{total}: PubMed ID {pubmed_id}")
                
                data = fetch_pubmed_data(pubmed_id)
                if data:
                    updated_data.append(data)
                else:
                    # If fetch fails, add basic info to maintain all records
                    basic_data = {
                        "PubmedID": pubmed_id,
                        "Title": row["Title"] if "Title" in df.columns else "Not Available",
                        "Publication Date": row["Publication Date"] if "Publication Date" in df.columns else "Not Available",
                        "Non-Academic Authors": row.get("Non-Academic Authors", ""),
                        "Company Affiliations": row.get("Company Affiliations", ""),
                        "Corresponding Author Email": "Not Available"
                    }
                    updated_data.append(basic_data)
                
                # Add a small delay to avoid overloading the NCBI server
                time.sleep(0.5)
            
            # Convert to DataFrame and save
            updated_df = pd.DataFrame(updated_data)
            
            # Replace any None/NaN values with empty strings to avoid NaN in output
            updated_df = updated_df.fillna("")
            
            updated_df.to_csv(output_file, index=False)
            print(f"Successfully updated data and saved to {output_file}")
            print("\nUpdated data sample:")
            print(updated_df.head())
        
        else:
            print("Skipping API update. Fixed data has been displayed.")
    
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()