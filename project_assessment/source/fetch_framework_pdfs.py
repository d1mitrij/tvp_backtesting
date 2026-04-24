import os
import requests
import time
from urllib.parse import urlparse

# Mapping of framework folders to their respective PDF URLs (Updated 2024/2025)
framework_pdfs = {
    "adb_framework_complete": [
        "https://www.adb.org/sites/default/files/linked-documents/crf-2025-2030-indicators-selection-overview-rationale.pdf",
        "https://www.adb.org/sites/default/files/institutional-document/991441/crf-indicator-definitions-2025-2030.pdf"
    ],
    "idb_framework_complete": [
        "https://publications.iadb.org/publications/english/document/Impact-Framework-2024-2030-Executive-Summary.pdf"
    ],
    "isdb_framework_complete": [
        "https://www.isdb.org/sites/default/files/media/documents/2025-05/Annual%20Development%20Effectiveness%20Report%202024.pdf"
    ],
    "ndb_framework_complete": [
        "https://www.ndb.int/wp-content/uploads/2024/10/NDB-Evaluation-Manual.pdf"
    ],
    "ebrd_framework_complete": [
        "https://www.mopanonline.org/assessments/ebrd2024/MOPAN_EBRD_Assessment_Report_2024.pdf",
        "https://www.ebrd.com/documents/strategy-and-policy-coordination/ebrd-impact-report-2024.pdf"
    ],
    "aiib_framework_complete": [
        "https://www.aiib.org/en/about-aiib/who-we-are/results-architecture/_download/AIIB-Results-Architecture.pdf"
    ],
    "aimm_framework_complete": [
        "https://documents1.worldbank.org/curated/en/614321627059462966/pdf/AIMM-General-Guidance-Note-Project-Assessment-and-Scoring-Guidance-Note.pdf"
    ]
}

# Browser-like headers to avoid 403 Forbidden errors
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def download_pdf(url, folder):
    """Downloads a PDF from a URL and saves it to a specified folder."""
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.basename(urlparse(url).path)
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        
        filepath = os.path.join(folder, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"File already exists: {filename}. Skipping.")
            return

        print(f"Downloading {url}...")
        
        # Using a session for better connection management
        session = requests.Session()
        response = session.get(url, headers=headers, stream=True, timeout=60)
        
        if response.status_code == 403:
            print(f"Access Forbidden (403) for {url}. The server is likely blocking this request.")
            return
        elif response.status_code == 404:
            print(f"Not Found (404) for {url}. The link may have moved.")
            return
            
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024): # 1MB chunks
                if chunk:
                    f.write(chunk)
        
        print(f"Successfully saved to: {filepath}")
        time.sleep(1) # Polite delay

    except Exception as e:
        print(f"Error downloading {url}: {e}")

def main():
    print("MDB PDF Downloader v2.0")
    for folder, urls in framework_pdfs.items():
        print(f"\nTarget Folder: {folder}")
        for url in urls:
            download_pdf(url, folder)

if __name__ == "__main__":
    main()
