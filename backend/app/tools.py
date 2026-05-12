from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .drive_service import GoogleDriveService
import re

class DriveTools:
    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
    
    def search_by_filename(self, filename: str, max_results: int = 20) -> List[Dict]:
        """Search files by filename within the designated folder"""
        return self.drive_service.search_files(
            query=filename, 
            max_results=max_results
        )
    
    def search_by_filetype(self, filetype: str, max_results: int = 20) -> List[Dict]:
        """Search files by file type (pdf, spreadsheet, image, etc.)"""
        # Map common terms to Google Drive mimeTypes
        type_mapping = {
            'spreadsheet': 'spreadsheet',
            'excel': 'spreadsheet',
            'sheet': 'spreadsheet',
            'image': 'image',
            'picture': 'image',
            'photo': 'image',
            'pdf': 'pdf',
            'presentation': 'presentation',
            'powerpoint': 'presentation',
            'slides': 'presentation',
            'document': 'document',
            'doc': 'document',
            'word': 'document'
        }
        
        mapped_type = type_mapping.get(filetype.lower(), filetype.lower())
        return self.drive_service.search_files(
            file_types=[mapped_type],
            max_results=max_results
        )
    
    def search_recent_files(self, days: int = 7, max_results: int = 20) -> List[Dict]:
        """Search files modified in the last N days"""
        return self.drive_service.get_recent_files(days=days, max_results=max_results)
    
    def search_all_files(self, max_results: int = 50) -> List[Dict]:
        """Get all files in the folder"""
        return self.drive_service.search_files(max_results=max_results)
    
    def search_in_folder(self, folder_name: str, max_results: int = 20) -> List[Dict]:
        """Search for files inside a specific subfolder"""
        # First find the folder by name
        all_items = self.drive_service.search_files(max_results=100)
        
        # Find the folder
        target_folder = None
        for item in all_items:
            if item.get('name', '').lower() == folder_name.lower() and 'folder' in item.get('mimeType', ''):
                target_folder = item
                break
        
        if not target_folder:
            return []
        
        # Store original folder ID
        original_folder_id = self.drive_service.folder_id
        
        # Temporarily change to subfolder
        self.drive_service.folder_id = target_folder['id']
        files = self.drive_service.search_files(max_results=max_results)
        
        # Restore original folder ID
        self.drive_service.folder_id = original_folder_id
        
        return files

def parse_user_intent(query: str) -> Dict:
    """Parse user query to determine search intent"""
    query_lower = query.lower()
    intent = {
        'search_type': 'general',
        'filters': {},
        'search_term': '',
        'response': None
    }
    
    # Check for "list all files" or similar
    if any(phrase in query_lower for phrase in ['list all', 'show all', 'all files', 'everything']):
        intent['search_type'] = 'all_files'
        return intent
    
    # Check for spreadsheet/excel queries
    if any(word in query_lower for word in ['spreadsheet', 'excel', 'sheet', 'xlsx']):
        intent['search_type'] = 'filetype'
        intent['filters']['file_type'] = 'spreadsheet'
        return intent
    
    # Check for image/photo queries
    if any(word in query_lower for word in ['image', 'picture', 'photo', 'jpg', 'png']):
        intent['search_type'] = 'filetype'
        intent['filters']['file_type'] = 'image'
        return intent
    
    # Check for PDF queries
    if any(word in query_lower for word in ['pdf', 'pdfs']):
        intent['search_type'] = 'filetype'
        intent['filters']['file_type'] = 'pdf'
        return intent
    
    # Check for presentation queries
    if any(word in query_lower for word in ['presentation', 'powerpoint', 'slides', 'ppt']):
        intent['search_type'] = 'filetype'
        intent['filters']['file_type'] = 'presentation'
        return intent
    
    # Check for invoice queries
    if 'invoice' in query_lower:
        intent['search_type'] = 'invoices'
        return intent
    
    # Check for recent files
    if any(word in query_lower for word in ['recent', 'new', 'latest', 'recently']):
        intent['search_type'] = 'recent'
        # Extract number of days if specified
        days_match = re.search(r'(\d+)\s*days?', query_lower)
        if days_match:
            intent['filters']['days'] = int(days_match.group(1))
        return intent
    
    # Check for date-based queries
    if any(word in query_lower for word in ['april', 'may', 'june', 'march']):
        intent['search_type'] = 'date'
        return intent
    
    # Default: search by filename
    # Extract search term
    patterns = [
        r'(?:find|search|show|get|list|look for|locate)\s+(?:me\s+)?(?:my\s+)?(?:all\s+)?(.+?)(?:\s+(?:from|in|that|which|with|by)$|$)',
        r'(?:looking for|need|want)\s+(?:my\s+)?(.+?)($)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            intent['search_term'] = match.group(1).strip()
            break
    
    if intent['search_term']:
        intent['search_type'] = 'filename'
    else:
        intent['search_type'] = 'general'
    
    return intent