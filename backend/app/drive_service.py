import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class GoogleDriveService:
    def __init__(self, service_account_file: str, folder_id: str):
        self.service_account_file = service_account_file
        self.folder_id = folder_id  # The specific folder to search
        self.service = None
        
    def authenticate(self):
        """Authenticate using Service Account (no user interaction)"""
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        self.service = build('drive', 'v3', credentials=credentials)
        return self.service
    
    def search_files(
        self, 
        query: str = "", 
        file_types: List[str] = None, 
        created_after: datetime = None,
        modified_after: datetime = None,
        max_results: int = 50
    ) -> List[Dict]:
        """Search within the specific folder using q parameter"""
        
        # Build the folder filter (ALWAYS include this)
        q_parts = [f"'{self.folder_id}' in parents"]
        
        # Build name filter (partial match)
        if query:
            q_parts.append(f"name contains '{query}'")
        
        # Build type filter (mimeType)
        if file_types:
            type_filters = []
            for ft in file_types:
                ft_lower = ft.lower()
                if ft_lower == 'pdf':
                    type_filters.append("mimeType='application/pdf'")
                elif ft_lower == 'document':
                    type_filters.append("mimeType='application/vnd.google-apps.document'")
                elif ft_lower == 'spreadsheet':
                    type_filters.append("mimeType='application/vnd.google-apps.spreadsheet'")
                elif ft_lower == 'presentation':
                    type_filters.append("mimeType='application/vnd.google-apps.presentation'")
                elif ft_lower == 'image':
                    type_filters.append("mimeType contains 'image/'")
            if type_filters:
                q_parts.append(f"({' or '.join(type_filters)})")
        
        # Build date filters (createdTime/modifiedTime)
        if created_after:
            q_parts.append(f"createdTime > '{created_after.isoformat()}'")
        if modified_after:
            q_parts.append(f"modifiedTime > '{modified_after.isoformat()}'")
        
        # Combine all filters
        full_query = " and ".join(q_parts)
        
        # Execute with proper q parameter
        results = self.service.files().list(
            q=full_query,
            spaces='drive',
            fields='files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)',
            pageSize=max_results
        ).execute()
        
        return results.get('files', [])
    
    def get_file_content(self, file_id: str) -> Optional[str]:
        """Get file content for text-based files"""
        try:
            file = self.service.files().get(fileId=file_id).execute()
            mime_type = file.get('mimeType', '')
            
            if 'text' in mime_type or 'document' in mime_type:
                content = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                ).execute()
                return content.decode('utf-8')
            return None
        except Exception as e:
            print(f"Error getting file content: {e}")
            return None
    
    def get_recent_files(self, days: int = 7, max_results: int = 50) -> List[Dict]:
        """Get recently modified files within the folder"""
        modified_after = datetime.now() - timedelta(days=days)
        return self.search_files(modified_after=modified_after, max_results=max_results)