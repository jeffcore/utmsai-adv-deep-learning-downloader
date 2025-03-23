#!/usr/bin/env python3
import os
import re
import requests
import time
import urllib.parse
import argparse
from bs4 import BeautifulSoup
from tqdm import tqdm


# URL of the course page
url = "https://ut.philkr.net/advances_in_deeplearning/"

# Function to sanitize filenames
def sanitize_filename(filename):
    # Remove characters that are not allowed in filenames
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Limit filename length
    if len(sanitized) > 150:
        sanitized = sanitized[:150]
    return sanitized

# Function to check if a file already exists
def file_exists(directory, filename):
    return os.path.exists(os.path.join(directory, filename))

# Function to download lecture slides
def download_slides(base_dir="adl-slides"):
    print("\n=== Downloading Lecture Slides ===")
    
    # Create the main download directory
    os.makedirs(base_dir, exist_ok=True)
    
    # Get the webpage content
    print("Fetching webpage content...")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all lecture links and their corresponding slide links
    print("Finding lecture slides...")
    lectures = []
    
    # Define the correct order of main sections
    main_sections = [
        "Getting Started",
        "Introduction",
        "Advanced Training",
        "Generative Models",
        "Large Language Models",
        "Computer Vision"
    ]
    
    # Find all section headers
    section_headers = soup.find_all(['h1', 'h2', 'h3'])
    
    # Process each section in order
    for section_name in main_sections:
        # Find section header
        section_header = None
        for header in section_headers:
            if header.text.strip() == section_name:
                section_header = header
                break
        
        if not section_header:
            continue
        
        # Find all lecture links within this section
        current = section_header.next_sibling
        while current:
            # Check if we've reached the next main section
            if current.name in ['h1', 'h2'] and current.text.strip() in main_sections:
                break
            
            # Look for lecture links
            if hasattr(current, 'find_all'):
                # Find lecture links
                for link in current.find_all('a'):
                    href = link.get('href')
                    if not href or not href.startswith(url):
                        continue
                    
                    # Check if this is a lecture page
                    if 'slides.pdf' in href:
                        # Extract module and lecture name from the URL
                        path_parts = href.replace(url, '').split('/')
                        if len(path_parts) >= 3:
                            module_name = path_parts[-3] if len(path_parts) >= 4 else ''
                            lecture_name = path_parts[-2].replace('_', ' ').title()
                            
                            # Add to lectures list
                            lectures.append({
                                'name': lecture_name,
                                'module': module_name,
                                'slides_url': href
                            })
                            
                            # Check for materials
                            materials_url = href.replace('slides.pdf', 'materials.zip')
                            try:
                                materials_response = requests.head(materials_url)
                                if materials_response.status_code == 200:
                                    lectures[-1]['materials_url'] = materials_url
                            except:
                                pass
            
            current = current.next_sibling
    
    # Alternative approach: look for all slide links directly
    if not lectures:
        print("Using alternative approach to find slides...")
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('slides.pdf'):
                slides_url = urllib.parse.urljoin(url, href)
                
                # Extract module and lecture name from the URL
                path_parts = href.split('/')
                if len(path_parts) >= 2:
                    module_name = path_parts[-3] if len(path_parts) >= 3 else ''
                    lecture_name = path_parts[-2].replace('_', ' ').title()
                    
                    lectures.append({
                        'name': lecture_name,
                        'module': module_name,
                        'slides_url': slides_url
                    })
                    
                    # Check for materials link
                    materials_url = slides_url.replace('slides.pdf', 'materials.zip')
                    try:
                        materials_response = requests.head(materials_url)
                        if materials_response.status_code == 200:
                            lectures[-1]['materials_url'] = materials_url
                    except:
                        pass
    
    # Print what we found
    print(f"Found {len(lectures)} lectures with slides")
    for lecture in lectures:
        print(f"- {lecture['name']}")
        if 'materials_url' in lecture:
            print(f"  (includes additional materials)")
    
    # Check which files already exist
    print("Checking for existing files...")
    existing_files = []
    for idx, lecture in enumerate(lectures, 1):
        module_part = f"{lecture.get('module', '')}_" if lecture.get('module') else ""
        filename = sanitize_filename(f"{idx:02d}_{module_part}{lecture['name']}.pdf")
        if file_exists(base_dir, filename):
            existing_files.append(filename)
        
        if 'materials_url' in lecture:
            materials_filename = sanitize_filename(f"{idx:02d}_{module_part}{lecture['name']}_materials.zip")
            if file_exists(base_dir, materials_filename):
                existing_files.append(materials_filename)
    
    if existing_files:
        print(f"Found {len(existing_files)} existing files that will be skipped.")
    
    # Download each lecture's slides and materials
    print("\nDownloading lecture slides and materials...")
    for idx, lecture in enumerate(tqdm(lectures, desc="Downloading"), 1):
        # Create numbered and sanitized filename based on module and lecture name
        module_part = f"{lecture.get('module', '')}_" if lecture.get('module') else ""
        filename = sanitize_filename(f"{idx:02d}_{module_part}{lecture['name']}.pdf")
        filepath = os.path.join(base_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            tqdm.write(f"Skipping {filename} (already exists)")
        else:
            # Download the slides
            try:
                slides_response = requests.get(lecture['slides_url'], stream=True)
                if slides_response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in slides_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    tqdm.write(f"Downloaded: {filename}")
                else:
                    tqdm.write(f"Failed to download {lecture['slides_url']}: HTTP {slides_response.status_code}")
                
                # Be nice to the server
                time.sleep(1)
            except Exception as e:
                tqdm.write(f"Error downloading {lecture['slides_url']}: {e}")
        
        # Download materials if available
        if 'materials_url' in lecture:
            module_part = f"{lecture.get('module', '')}_" if lecture.get('module') else ""
            materials_filename = sanitize_filename(f"{idx:02d}_{module_part}{lecture['name']}_materials.zip")
            materials_filepath = os.path.join(base_dir, materials_filename)
            
            # Skip if file already exists
            if os.path.exists(materials_filepath):
                tqdm.write(f"Skipping {materials_filename} (already exists)")
            else:
                # Download the materials
                try:
                    materials_response = requests.get(lecture['materials_url'], stream=True)
                    if materials_response.status_code == 200:
                        with open(materials_filepath, 'wb') as f:
                            for chunk in materials_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        tqdm.write(f"Downloaded: {materials_filename}")
                    else:
                        tqdm.write(f"Failed to download {lecture['materials_url']}: HTTP {materials_response.status_code}")
                    
                    # Be nice to the server
                    time.sleep(1)
                except Exception as e:
                    tqdm.write(f"Error downloading {lecture['materials_url']}: {e}")
    
    print("\nSlides download complete!")

# Function to download research papers
def download_papers(base_dir="adl-papers"):
    print("\n=== Downloading Research Papers ===")
    
    # Create the main download directory
    os.makedirs(base_dir, exist_ok=True)
    
    # Get the webpage content
    print("Fetching webpage content...")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the References section
    references_section = None
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        if header.text.strip() == "References":
            references_section = header
            break
    
    if not references_section:
        print("References section not found on the page.")
        return
    
    # Get all list items after the References header
    papers = []
    ref_items = []
    
    # Find the list containing references
    for element in references_section.find_next_siblings():
        if element.name == 'ol':
            ref_items = element.find_all('li')
            break
    
    if not ref_items:
        # Try another approach - look for divs with reference-like content
        current = references_section.next_sibling
        while current and not ref_items:
            if hasattr(current, 'find_all'):
                # Look for numbered items that might be references
                potential_refs = current.find_all('p')
                if potential_refs:
                    ref_items = potential_refs
            current = current.next_sibling
    
    # Regular expressions for matching arxiv links
    arxiv_pattern = re.compile(r'https://arxiv.org/abs/(\d+\.\d+)(v\d+)?')
    arxiv_pdf_pattern = re.compile(r'https://arxiv.org/pdf/(\d+\.\d+)(v\d+)?\.pdf')
    
    # If we still don't have reference items, scan the entire page after the References section
    if not ref_items:
        print("Scanning entire page for references...")
        # Get all elements after the References section
        current = references_section.next_sibling
        ref_num = 1  # Start with reference 1
        
        while current:
            # Check if this element contains an arxiv link
            if hasattr(current, 'find_all'):
                for link in current.find_all('a'):
                    href = link.get('href')
                    if href and (arxiv_pattern.match(href) or arxiv_pdf_pattern.match(href)):
                        # Extract the arxiv ID
                        if 'pdf' in href:
                            arxiv_id = arxiv_pdf_pattern.match(href).group(1)
                            pdf_url = href
                        else:
                            arxiv_id = arxiv_pattern.match(href).group(1)
                            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                        
                        # Try to find reference number in text
                        parent_text = link.parent.get_text() if link.parent else ""
                        ref_match = re.search(r'(\d+)\.', parent_text)
                        if ref_match:
                            ref_num = int(ref_match.group(1))
                        
                        # Extract title and authors
                        title_author = parent_text.replace(href, "").strip()
                        if not title_author:
                            title_author = f"Reference {ref_num}"
                        
                        papers.append({
                            'ref_num': ref_num,
                            'arxiv_id': arxiv_id,
                            'title_author': title_author,
                            'url': pdf_url
                        })
                        
                        ref_num += 1  # Increment for next reference
            current = current.next_sibling
    else:
        # Process each reference item
        for i, item in enumerate(ref_items):
            ref_num = i + 1  # Reference numbers start at 1
            item_text = item.get_text()
            
            # Look for arxiv links in this reference
            arxiv_links = []
            for link in item.find_all('a'):
                href = link.get('href')
                if href and arxiv_pattern.match(href):
                    arxiv_links.append((link, href, arxiv_pattern.match(href).group(1)))
                elif href and arxiv_pdf_pattern.match(href):
                    arxiv_links.append((link, href, arxiv_pdf_pattern.match(href).group(1)))
            
            # Process each arxiv link found
            for link, href, arxiv_id in arxiv_links:
                # Create PDF URL
                if 'pdf' in href:
                    pdf_url = href
                else:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                # Extract title and authors
                title_author = item_text
                # Try to clean up the title
                title_match = re.search(r'\[(.*?)\]', title_author)
                if title_match:
                    title_author = title_match.group(1)
                else:
                    # Remove the URL and clean up
                    title_author = title_author.replace(href, "").strip()
                
                papers.append({
                    'ref_num': ref_num,
                    'arxiv_id': arxiv_id,
                    'title_author': title_author,
                    'url': pdf_url
                })
    
    # Print what we found for debugging
    for paper in papers:
        print(f"Found paper: #{paper['ref_num']} - {paper['title_author']} (arxiv:{paper['arxiv_id']})")
    
    # Sort papers by reference number
    papers.sort(key=lambda x: x['ref_num'])
    
    # Remove duplicates (same arxiv ID)
    unique_papers = []
    seen_ids = set()
    for paper in papers:
        if paper['arxiv_id'] not in seen_ids:
            unique_papers.append(paper)
            seen_ids.add(paper['arxiv_id'])
    
    print(f"Found {len(unique_papers)} unique papers to download.")
    
    # Download each paper
    print("\nDownloading papers...")
    for paper in tqdm(unique_papers):
        # Extract just the title (remove authors)
        title = paper['title_author']
        
        # Remove any author names that might be in the title
        # Common patterns: "Title - Authors", "Title: Authors", "Title, Authors"
        for separator in [' - ', ', ', ': ']:
            if separator in title:
                title = title.split(separator)[0].strip()
        
        # Remove any remaining author names (often in parentheses)
        title = re.sub(r'\([^)]*\)', '', title).strip()
        
        # Clean up the title further
        title = re.sub(r'\s+', '_', title)  # Replace spaces with underscores
        title = re.sub(r'[^a-zA-Z0-9_-]', '', title)  # Remove special characters
        
        # Limit title length to avoid excessively long filenames
        title = title[:30] if len(title) > 30 else title
        
        # Create a clean filename with reference number, short title, and arxiv ID
        filename = f"{paper['ref_num']:03d}_{title}_{paper['arxiv_id']}.pdf"
        filepath = os.path.join(base_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            tqdm.write(f"Skipping {filename} (already exists)")
            continue
        
        # Download the PDF
        try:
            pdf_response = requests.get(paper['url'], stream=True)
            if pdf_response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                tqdm.write(f"Downloaded: {filename}")
            else:
                tqdm.write(f"Failed to download {paper['url']}: HTTP {pdf_response.status_code}")
            
            # Be nice to the server
            time.sleep(1)
        except Exception as e:
            tqdm.write(f"Error downloading {paper['url']}: {e}")
    
    print("\nPapers download complete!")

def main():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Download lecture slides and research papers from the Advances in Deep Learning course.')
    parser.add_argument('--slides', action='store_true', help='Download lecture slides')
    parser.add_argument('--papers', action='store_true', help='Download research papers')
    parser.add_argument('--slides-dir', default='adl-slides', help='Directory to save slides (default: adl-slides)')
    parser.add_argument('--papers-dir', default='adl-papers', help='Directory to save papers (default: adl-papers)')
    
    args = parser.parse_args()
    
    # If no specific options are provided, download both
    if not args.slides and not args.papers:
        args.slides = True
        args.papers = True
    
    # Download slides if requested
    if args.slides:
        download_slides(args.slides_dir)
    
    # Download papers if requested
    if args.papers:
        download_papers(args.papers_dir)
    
    print("\nAll downloads complete!")

if __name__ == "__main__":
    main()
