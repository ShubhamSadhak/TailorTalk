from datetime import datetime
from typing import List, Dict

def format_file_size(size_bytes: int) -> str:
    """Format file size from bytes to human readable format"""
    if not size_bytes:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def extract_date_from_query(query: str) -> Dict:
    """Extract date information from natural language query"""
    import re
    from datetime import datetime, timedelta
    
    query_lower = query.lower()
    date_info = {}
    
    # Look for specific dates
    date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
    match = re.search(date_pattern, query)
    if match:
        try:
            date_info['specific_date'] = datetime.strptime(match.group(1), "%m/%d/%Y")
        except:
            pass
    
    # Look for relative dates
    if 'yesterday' in query_lower:
        date_info['start_date'] = datetime.now() - timedelta(days=1)
        date_info['end_date'] = datetime.now()
    elif 'today' in query_lower:
        date_info['start_date'] = datetime.now().replace(hour=0, minute=0, second=0)
        date_info['end_date'] = datetime.now()
    
    return date_info

def categorize_file(mime_type: str) -> str:
    """Categorize file based on MIME type"""
    categories = {
        'document': ['document', 'text', 'pdf', 'word'],
        'spreadsheet': ['sheet', 'excel', 'csv'],
        'presentation': ['presentation', 'slides', 'powerpoint'],
        'image': ['image', 'photo', 'picture'],
        'video': ['video', 'movie'],
        'audio': ['audio', 'sound', 'music'],
        'archive': ['zip', 'rar', 'tar', 'gz']
    }
    
    mime_lower = mime_type.lower()
    for category, keywords in categories.items():
        if any(keyword in mime_lower for keyword in keywords):
            return category
    
    return 'other'