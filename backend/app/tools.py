from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .drive_service import GoogleDriveService
import re

class DriveTools:
    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
    
    def search_by_filename(self, filename: str, max_results: int = 20) -> List[Dict]:
        """Search files by filename"""
        return self.drive_service.search_files(query=filename, max_results=max_results)
    
    def search_by_filetype(self, filetype: str, max_results: int = 20) -> List[Dict]:
        """Search files by file type"""
        # Normalize file type
        filetype_lower = filetype.lower()
        
        # Map common terms
        if filetype_lower in ['spreadsheet', 'excel', 'sheet', 'xlsx']:
            return self.drive_service.search_files(file_types=['spreadsheet'], max_results=max_results)
        elif filetype_lower in ['image', 'picture', 'photo']:
            return self.drive_service.search_files(file_types=['image'], max_results=max_results)
        elif filetype_lower in ['pdf']:
            return self.drive_service.search_files(file_types=['pdf'], max_results=max_results)
        elif filetype_lower in ['presentation', 'powerpoint', 'slides']:
            return self.drive_service.search_files(file_types=['presentation'], max_results=max_results)
        else:
            return self.drive_service.search_files(file_types=[filetype], max_results=max_results)
    
    def search_recent_files(self, days: int = 7, max_results: int = 20) -> List[Dict]:
        """Search files modified in the last N days"""
        return self.drive_service.get_recent_files(days=days, max_results=max_results)
    
    def search_all_files(self, max_results: int = 50) -> List[Dict]:
        """Get all files in the folder"""
        return self.drive_service.search_files(max_results=max_results)
    
    def search_in_folder(self, folder_name: str, max_results: int = 20) -> List[Dict]:
        """Search for files inside a specific subfolder"""
        all_items = self.drive_service.search_files(max_results=100)
        
        target_folder = None
        for item in all_items:
            if item.get('name', '').lower() == folder_name.lower() and 'folder' in item.get('mimeType', ''):
                target_folder = item
                break
        
        if not target_folder:
            return []
        
        original_folder_id = self.drive_service.folder_id
        self.drive_service.folder_id = target_folder['id']
        files = self.drive_service.search_files(max_results=max_results)
        self.drive_service.folder_id = original_folder_id
        
        return files

def parse_user_intent(query: str) -> Dict:
    """Parse user query to determine search intent"""
    query_lower = query.lower()
    intent = {
        'search_type': 'general',
        'filters': {},
        'search_term': '',
    }
    
    # Check for spreadsheet queries
    if any(word in query_lower for word in ['spreadsheet', 'excel', 'sheet', 'xlsx']):
        intent['search_type'] = 'filetype'
        intent['filters']['file_type'] = 'spreadsheet'
        return intent
    
    # Check for image queries
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
    if any(word in query_lower for word in ['presentation', 'powerpoint', 'slides']):
        intent['search_type'] = 'filetype'
        intent['filters']['file_type'] = 'presentation'
        return intent
    
    # Check for list all files
    if any(word in query_lower for word in ['list all', 'show all', 'all files']):
        intent['search_type'] = 'all_files'
        return intent
    
    # Check for invoices folder
    if 'invoice' in query_lower:
        intent['search_type'] = 'invoices'
        return intent
    
    # Check for recent files
    if any(word in query_lower for word in ['recent', 'new', 'latest']):
        intent['search_type'] = 'recent'
        days = 7
        days_match = re.search(r'(\d+)\s*days?', query_lower)
        if days_match:
            days = int(days_match.group(1))
        intent['filters']['days'] = days
        return intent
    
    # Default: search by filename
    patterns = [
        r'(?:find|search|show|get|list|look for|locate)\s+(?:me\s+)?(?:my\s+)?(?:all\s+)?(.+?)$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            intent['search_term'] = match.group(1).strip()
            break
    
    if intent['search_term']:
        intent['search_type'] = 'filename'
    
    return intent