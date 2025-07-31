import os
import re
import requests
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EducationalResourceScraper:
    """
    Scraper for South African educational resources from trusted websites
    """
    
    def __init__(self, base_dir: str = "resources"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create metadata file to track downloads
        self.metadata_file = self.base_dir / "metadata.json"
        self.metadata = self.load_metadata()
        
        # Grade and subject mappings
        self.grades = ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "ABET"]
        self.subjects = [
            "Mathematics", "Physical Science", "Life Sciences", "English", 
            "Afrikaans", "History", "Geography", "Business Studies",
            "Accounting", "Economics", "Life Orientation"
        ]
        
        # Resource types
        self.resource_types = ["Textbook", "Teacher Guide", "Past Exam", "Worksheet", "Study Guide"]
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def load_metadata(self) -> Dict:
        """Load metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {"downloads": {}, "last_update": None}
    
    def save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def get_file_hash(self, content: bytes) -> str:
        """Generate hash for file content to detect changes"""
        return hashlib.md5(content).hexdigest()
    
    def categorize_file(self, filename: str, url: str = "") -> Tuple[str, str, str]:
        """
        Categorize file by grade, subject, and type based on filename and URL
        Returns: (grade, subject, resource_type)
        """
        filename_lower = filename.lower()
        url_lower = url.lower()
        combined = f"{filename_lower} {url_lower}"
        
        # Detect grade
        grade = "Unknown"
        for g in self.grades:
            grade_num = re.search(r'grade\s*(\d+)', combined)
            if grade_num and g.endswith(grade_num.group(1)):
                grade = g
                break
            elif g.lower().replace(" ", "") in combined.replace(" ", ""):
                grade = g
                break
        
        # Detect subject
        subject = "General"
        for s in self.subjects:
            if s.lower() in combined or s.lower().replace(" ", "") in combined.replace(" ", ""):
                subject = s
                break
        
        # Detect resource type
        resource_type = "Document"
        if any(word in combined for word in ["textbook", "book", "manual"]):
            resource_type = "Textbook"
        elif any(word in combined for word in ["teacher", "guide", "educator"]):
            resource_type = "Teacher Guide"
        elif any(word in combined for word in ["exam", "test", "paper", "memorandum"]):
            resource_type = "Past Exam"
        elif any(word in combined for word in ["worksheet", "exercise", "activity"]):
            resource_type = "Worksheet"
        elif any(word in combined for word in ["study", "revision", "summary"]):
            resource_type = "Study Guide"
        
        return grade, subject, resource_type
    
    def create_folder_structure(self, grade: str, subject: str, resource_type: str) -> Path:
        """Create and return the folder path for a resource"""
        folder_path = self.base_dir / grade / subject / resource_type
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path
    
    def download_file(self, url: str, filename: str, grade: str, subject: str, resource_type: str, source: str) -> bool:
        """Download a file and save it in the appropriate folder"""
        try:
            # Create folder structure
            folder_path = self.create_folder_structure(grade, subject, resource_type)
            file_path = folder_path / filename
            
            # Check if file already exists and is up to date
            file_key = f"{grade}/{subject}/{resource_type}/{filename}"
            
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get file content
            content = response.content
            file_hash = self.get_file_hash(content)
            
            # Check if file has changed
            if file_key in self.metadata["downloads"]:
                if self.metadata["downloads"][file_key]["hash"] == file_hash:
                    logger.info(f"File unchanged: {filename}")
                    return True
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Update metadata
            self.metadata["downloads"][file_key] = {
                "url": url,
                "filename": filename,
                "grade": grade,
                "subject": subject,
                "resource_type": resource_type,
                "source": source,
                "download_date": datetime.now().isoformat(),
                "file_size": len(content),
                "hash": file_hash
            }
            
            logger.info(f"Downloaded: {filename} -> {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    def scrape_siyavula(self) -> List[Dict]:
        """Scrape resources from Siyavula"""
        resources = []
        base_url = "https://www.siyavula.com"
        
        try:
            # Siyavula textbook pages
            textbook_urls = [
                "/read/maths/grade-10",
                "/read/maths/grade-11", 
                "/read/maths/grade-12",
                "/read/science/grade-10",
                "/read/science/grade-11",
                "/read/science/grade-12"
            ]
            
            for path in textbook_urls:
                try:
                    url = urljoin(base_url, path)
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for PDF download links
                    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
                    
                    for link in pdf_links:
                        pdf_url = urljoin(url, link.get('href'))
                        filename = os.path.basename(urlparse(pdf_url).path)
                        
                        if filename and filename.endswith('.pdf'):
                            grade, subject, resource_type = self.categorize_file(filename, pdf_url)
                            
                            resources.append({
                                'url': pdf_url,
                                'filename': filename,
                                'grade': grade,
                                'subject': subject,
                                'resource_type': resource_type,
                                'source': 'Siyavula'
                            })
                    
                    time.sleep(1)  # Be respectful to the server
                    
                except Exception as e:
                    logger.error(f"Error scraping Siyavula path {path}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Siyavula: {e}")
        
        return resources
    
    def scrape_dbe_resources(self) -> List[Dict]:
        """Scrape resources from Department of Basic Education"""
        resources = []
        base_url = "https://www.education.gov.za"
        
        try:
            # Common DBE resource pages
            resource_pages = [
                "/Curriculum/NationalSeniorCertificate/NSCPastExaminationpapers.aspx",
                "/Curriculum/LearningandTeachingSupportMaterials(LTSM).aspx"
            ]
            
            for page in resource_pages:
                try:
                    url = urljoin(base_url, page)
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for PDF and document links
                    doc_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
                    
                    for link in doc_links:
                        doc_url = urljoin(url, link.get('href'))
                        filename = os.path.basename(urlparse(doc_url).path)
                        
                        if filename:
                            grade, subject, resource_type = self.categorize_file(filename, doc_url)
                            
                            resources.append({
                                'url': doc_url,
                                'filename': filename,
                                'grade': grade,
                                'subject': subject,
                                'resource_type': resource_type,
                                'source': 'Department of Basic Education'
                            })
                    
                    time.sleep(2)  # Be respectful to the server
                    
                except Exception as e:
                    logger.error(f"Error scraping DBE page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping DBE: {e}")
        
        return resources
    
    def scrape_wced_portal(self) -> List[Dict]:
        """Scrape resources from WCED Portal"""
        resources = []
        base_url = "https://wcedeportal.co.za"
        
        try:
            # WCED resource sections
            sections = [
                "/curriculum/senior-phase",
                "/curriculum/fet-phase",
                "/resources/past-papers"
            ]
            
            for section in sections:
                try:
                    url = urljoin(base_url, section)
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for resource links
                    resource_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
                    
                    for link in resource_links:
                        resource_url = urljoin(url, link.get('href'))
                        filename = os.path.basename(urlparse(resource_url).path)
                        
                        if filename:
                            grade, subject, resource_type = self.categorize_file(filename, resource_url)
                            
                            resources.append({
                                'url': resource_url,
                                'filename': filename,
                                'grade': grade,
                                'subject': subject,
                                'resource_type': resource_type,
                                'source': 'Western Cape Education Department'
                            })
                    
                    time.sleep(2)  # Be respectful to the server
                    
                except Exception as e:
                    logger.error(f"Error scraping WCED section {section}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping WCED: {e}")
        
        return resources
    
    def scrape_thutong(self) -> List[Dict]:
        """Scrape resources from Thutong portal"""
        resources = []
        base_url = "http://www.thutong.doe.gov.za"
        
        try:
            # Thutong resource sections
            sections = [
                "/ResourceDownload.aspx",
                "/TeacherDevelopment.aspx"
            ]
            
            for section in sections:
                try:
                    url = urljoin(base_url, section)
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for downloadable resources
                    download_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
                    
                    for link in download_links:
                        download_url = urljoin(url, link.get('href'))
                        filename = os.path.basename(urlparse(download_url).path)
                        
                        if filename:
                            grade, subject, resource_type = self.categorize_file(filename, download_url)
                            
                            resources.append({
                                'url': download_url,
                                'filename': filename,
                                'grade': grade,
                                'subject': subject,
                                'resource_type': resource_type,
                                'source': 'Thutong Portal'
                            })
                    
                    time.sleep(2)  # Be respectful to the server
                    
                except Exception as e:
                    logger.error(f"Error scraping Thutong section {section}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Thutong: {e}")
        
        return resources
    
    def run_full_scrape(self) -> Dict:
        """Run full scrape of all sources"""
        logger.info("Starting full resource scrape...")
        
        all_resources = []
        
        # Scrape all sources
        logger.info("Scraping Siyavula...")
        all_resources.extend(self.scrape_siyavula())
        
        logger.info("Scraping Department of Basic Education...")
        all_resources.extend(self.scrape_dbe_resources())
        
        logger.info("Scraping WCED Portal...")
        all_resources.extend(self.scrape_wced_portal())
        
        logger.info("Scraping Thutong Portal...")
        all_resources.extend(self.scrape_thutong())
        
        # Download all resources
        successful_downloads = 0
        failed_downloads = 0
        
        for resource in all_resources:
            success = self.download_file(
                resource['url'],
                resource['filename'],
                resource['grade'],
                resource['subject'],
                resource['resource_type'],
                resource['source']
            )
            
            if success:
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            # Small delay between downloads
            time.sleep(0.5)
        
        # Update metadata
        self.metadata["last_update"] = datetime.now().isoformat()
        self.save_metadata()
        
        result = {
            "total_resources_found": len(all_resources),
            "successful_downloads": successful_downloads,
            "failed_downloads": failed_downloads,
            "last_update": self.metadata["last_update"]
        }
        
        logger.info(f"Scrape completed: {result}")
        return result

if __name__ == "__main__":
    scraper = EducationalResourceScraper()
    result = scraper.run_full_scrape()
    print(f"Scraping completed: {result}")
