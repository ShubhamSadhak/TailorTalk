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
        """Search files by file type (pdf, document, spreadsheet, presentation, image)"""
        return self.drive_service.search_files(
            file_types=[filetype],
            max_results=max_results
        )
    
    def search_by_date_range(
        self,
        start_date: str = None,
        end_date: str = None,
        max_results: int = 20
    ) -> List[Dict]:
        """Search files created or modified within a date range"""
        created_after = None
        modified_after = None
        
        if start_date:
            created_after = datetime.strptime(start_date, "%Y-%m-%d")
            modified_after = datetime.strptime(start_date, "%Y-%m-%d")
        
        if end_date:
            # This would need more complex filtering for end dates
            pass
        
        return self.drive_service.search_files(
            created_after=created_after,
            modified_after=modified_after,
            max_results=max_results
        )
    
    def search_recent_files(self, days: int = 7, max_results: int = 20) -> List[Dict]:
        """Search files modified in the last N days"""
        return self.drive_service.get_recent_files(days=days, max_results=max_results)
    
    def search_by_extension(self, extension: str, max_results: int = 20) -> List[Dict]:
        """Search files by file extension (pdf, docx, xlsx, pptx, etc.)"""
        return self.drive_service.search_files(query=f"*{extension}", max_results=max_results)
    
    def search_files_by_content(self, search_text: str, max_results: int = 20) -> List[Dict]:
        """Search within file content (for text-based files)"""
        files = self.drive_service.search_files(max_results=max_results)
        matching_files = []
        
        for file in files:
            content = self.drive_service.get_file_content(file['id'])
            if content and search_text.lower() in content.lower():
                matching_files.append(file)
                if len(matching_files) >= max_results:
                    break
        
        return matching_files

def parse_user_intent(query: str) -> Dict:
    """Parse user query to determine search intent"""
    query_lower = query.lower()
    intent = {
        'search_type': 'general',
        'filters': {},
        'search_term': ''
    }
    
    # Extract search term (remove common query patterns)
    patterns = [
        r'(?:find|search|show|get|list|look for|locate)\s+(?:me\s+)?(?:my\s+)?(?:all\s+)?(.+?)(?:\s+(?:from|in|that|which|with|by)$|$)',
        r'(?:looking for|need|want)\s+(?:my\s+)?(.+?)($)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            intent['search_term'] = match.group(1).strip()
            break
    
    # Determine file type
    file_types = {
        'pdf': ['pdf', 'pdfs', 'pdf files', 'pdf documents'],
        'document': ['document', 'documents', 'doc', 'docs', 'word', 'text file', 'txt'],
        'spreadsheet': ['spreadsheet', 'spreadsheets', 'excel', 'sheet', 'sheets', 'xlsx'],
        'presentation': ['presentation', 'presentations', 'powerpoint', 'slides', 'ppt', 'pptx'],
        'image': ['image', 'images', 'picture', 'pictures', 'photo', 'photos', 'jpg', 'png']
    }
    
    for file_type, keywords in file_types.items():
        if any(keyword in query_lower for keyword in keywords):
            intent['filters']['file_type'] = file_type
            break
    
    # Determine date filters
    date_patterns = {
        'today': r'\b(?:today|latest|just now)\b',
        'yesterday': r'\byesterday\b',
        'last_week': r'\b(?:last week|past week|recent|previous week)\b',
        'last_month': r'\b(?:last month|past month|previous month)\b',
        'last_3_months': r'\b(?:last 3 months|past 3 months|recent months)\b',
        'last_year': r'\b(?:last year|past year)\b'
    }
    
    for date_range, pattern in date_patterns.items():
        if re.search(pattern, query_lower):
            intent['filters']['date_range'] = date_range
            break
    
    # Determine if searching by content
    if any(keyword in query_lower for keyword in ['contains', 'has the words', 'includes', 'text']):
        intent['filters']['search_in_content'] = True
    
    return intent
