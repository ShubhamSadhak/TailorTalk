from typing import List, Dict, Optional, Type
from datetime import datetime, timedelta
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from .drive_service import GoogleDriveService
import re

# Define input schemas for each tool
class FilenameInput(BaseModel):
    filename: str = Field(description="The filename or partial filename to search for")
    max_results: int = Field(default=20, description="Maximum number of results to return")

class FiletypeInput(BaseModel):
    filetype: str = Field(description="File type to search for (pdf, document, spreadsheet, presentation, image)")
    max_results: int = Field(default=20, description="Maximum number of results to return")

class RecentFilesInput(BaseModel):
    days: int = Field(default=7, description="Number of days to look back")
    max_results: int = Field(default=20, description="Maximum number of results to return")

class ContentInput(BaseModel):
    search_text: str = Field(description="Text to search for within file content")
    max_results: int = Field(default=20, description="Maximum number of results to return")

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
        """Search files by file type (pdf, document, spreadsheet, presentation, image)"""
        return self.drive_service.search_files(
            file_types=[filetype],
            max_results=max_results
        )
    
    def search_recent_files(self, days: int = 7, max_results: int = 20) -> List[Dict]:
        """Search files modified in the last N days"""
        return self.drive_service.get_recent_files(days=days, max_results=max_results)
    
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
    
    def search_all_files(self, max_results: int = 50) -> List[Dict]:
        """Get all files in the folder"""
        return self.drive_service.search_files(max_results=max_results)

# Create LangChain-compatible tool wrappers
def create_tools(drive_tools: DriveTools):
    """Create LangChain tools from DriveTools instance"""
    
    from langchain.tools import tool
    
    @tool
    def search_pdf_files(max_results: int = 20) -> str:
        """Search for PDF files in the folder"""
        results = drive_tools.search_by_filetype('pdf', max_results)
        if results:
            file_list = '\n'.join([f"- {f['name']} (Modified: {f.get('modifiedTime', 'Unknown')[:10]})" for f in results])
            return f"Found {len(results)} PDF files:\n{file_list}"
        return "No PDF files found in the folder."
    
    @tool
    def search_spreadsheet_files(max_results: int = 20) -> str:
        """Search for spreadsheet files (Excel, Sheets) in the folder"""
        results = drive_tools.search_by_filetype('spreadsheet', max_results)
        if results:
            file_list = '\n'.join([f"- {f['name']}" for f in results])
            return f"Found {len(results)} spreadsheet files:\n{file_list}"
        return "No spreadsheet files found in the folder."
    
    @tool
    def search_image_files(max_results: int = 20) -> str:
        """Search for image files in the folder"""
        results = drive_tools.search_by_filetype('image', max_results)
        if results:
            file_list = '\n'.join([f"- {f['name']}" for f in results])
            return f"Found {len(results)} image files:\n{file_list}"
        return "No image files found in the folder."
    
    @tool
    def search_by_filename_tool(filename: str, max_results: int = 20) -> str:
        """Search files by filename (partial match allowed)"""
        results = drive_tools.search_by_filename(filename, max_results)
        if results:
            file_list = '\n'.join([f"- {f['name']}" for f in results])
            return f"Found {len(results)} files matching '{filename}':\n{file_list}"
        return f"No files found matching '{filename}'."
    
    @tool
    def search_recent_files_tool(days: int = 7, max_results: int = 20) -> str:
        """Search files modified in the last N days"""
        results = drive_tools.search_recent_files(days, max_results)
        if results:
            file_list = '\n'.join([f"- {f['name']} (Modified: {f.get('modifiedTime', 'Unknown')[:10]})" for f in results])
            return f"Found {len(results)} files modified in the last {days} days:\n{file_list}"
        return f"No files found modified in the last {days} days."
    
    @tool
    def list_all_files(max_results: int = 30) -> str:
        """List all files in the Google Drive folder"""
        results = drive_tools.search_all_files(max_results)
        if results:
            # Group by file type
            pdfs = [f for f in results if f.get('mimeType') == 'application/pdf']
            spreadsheets = [f for f in results if 'spreadsheet' in f.get('mimeType', '')]
            images = [f for f in results if 'image' in f.get('mimeType', '')]
            others = [f for f in results if f not in pdfs and f not in spreadsheets and f not in images]
            
            response = f"📁 Folder contains {len(results)} files:\n\n"
            
            if pdfs:
                response += f"📄 PDF Files ({len(pdfs)}):\n"
                for f in pdfs[:5]:
                    response += f"   - {f['name']}\n"
                response += "\n"
            
            if spreadsheets:
                response += f"📊 Spreadsheets ({len(spreadsheets)}):\n"
                for f in spreadsheets[:5]:
                    response += f"   - {f['name']}\n"
                response += "\n"
            
            if images:
                response += f"🖼️ Images ({len(images)}):\n"
                for f in images[:5]:
                    response += f"   - {f['name']}\n"
                response += "\n"
            
            if others:
                response += f"📎 Other Files ({len(others)}):\n"
                for f in others[:5]:
                    response += f"   - {f['name']}\n"
            
            return response
        return "No files found in the folder."
    
    @tool
    def search_invoices() -> str:
        """Search for invoice-related files (looks in 'invoices' folder or files with 'invoice' in name)"""
        # First try to find files with 'invoice' in name
        results = drive_tools.search_by_filename('invoice', 20)
        if results:
            file_list = '\n'.join([f"- {f['name']}" for f in results])
            return f"Found {len(results)} invoice files:\n{file_list}"
        
        # Check if there's an 'invoices' folder and list its contents
        all_files = drive_tools.search_all_files(100)
        invoice_folder = None
        for file in all_files:
            if file.get('name', '').lower() == 'invoices' and file.get('mimeType') == 'application/vnd.google-apps.folder':
                invoice_folder = file
                break
        
        if invoice_folder:
            # Search within the invoices folder
            original_folder = drive_tools.drive_service.folder_id
            drive_tools.drive_service.folder_id = invoice_folder['id']
            folder_files = drive_tools.search_all_files(50)
            drive_tools.drive_service.folder_id = original_folder
            
            if folder_files:
                file_list = '\n'.join([f"- {f['name']}" for f in folder_files])
                return f"Found 'invoices' folder with {len(folder_files)} files:\n{file_list}"
            else:
                return "Found 'invoices' folder but it is empty."
        
        return "No invoice files or 'invoices' folder found."
    
    return [
        search_pdf_files,
        search_spreadsheet_files,
        search_image_files,
        search_by_filename_tool,
        search_recent_files_tool,
        list_all_files,
        search_invoices,
    ]

def parse_user_intent(query: str) -> Dict:
    """Parse user query to determine search intent"""
    query_lower = query.lower()
    intent = {
        'search_type': 'general',
        'filters': {},
        'search_term': ''
    }
    
    # Check for specific queries first
    if 'invoice' in query_lower:
        intent['search_type'] = 'invoices'
        intent['search_term'] = 'invoices'
        return intent
    
    if 'all files' in query_lower or 'list all' in query_lower or 'show all' in query_lower:
        intent['search_type'] = 'all_files'
        return intent
    
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
    
    # Determine file type
    file_types = {
        'pdf': ['pdf', 'pdfs', 'pdf files', 'pdf documents'],
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
    
    return intent