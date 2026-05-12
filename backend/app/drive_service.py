import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class GoogleDriveService:
    def __init__(self, service_account_file: str = None, folder_id: str = None):
        self.service_account_file = service_account_file
        self.folder_id = folder_id
        self.service = None
        
    def authenticate(self):
        """Authenticate using Service Account from file or environment variable"""
        try:
            credentials = None
            
            # Try to get credentials from environment variable
            creds_json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if creds_json_str:
                try:
                    creds_dict = json.loads(creds_json_str)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict,
                        scopes=['https://www.googleapis.com/auth/drive.readonly']
                    )
                except Exception as e:
                    print(f"Error loading credentials from env: {e}")
            
            # Fall back to file
            if not credentials and self.service_account_file and os.path.exists(self.service_account_file):
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            
            if not credentials:
                raise Exception("No valid credentials found")
            
            self.service = build('drive', 'v3', credentials=credentials)
            return self.service
            
        except Exception as e:
            print(f"Authentication error: {e}")
            raise e
    
    def search_files(
        self, 
        query: str = "", 
        file_types: List[str] = None, 
        created_after: datetime = None,
        modified_after: datetime = None,
        max_results: int = 50
    ) -> List[Dict]:
        """Search within the specific folder using q parameter"""
        
        if not self.folder_id:
            raise Exception("DRIVE_FOLDER_ID is not set")
        
        # Build the folder filter
        q_parts = [f"'{self.folder_id}' in parents"]
        
        # Build name filter
        if query:
            safe_query = query.replace("'", "\\'")
            q_parts.append(f"name contains '{safe_query}'")
        
        # Build type filter - FIXED: Map properly to Google Drive mimeTypes
        if file_types:
            type_filters = []
            for ft in file_types:
                ft_lower = ft.lower()
                # Map common file types to Google Drive mimeTypes
                if ft_lower in ['spreadsheet', 'excel', 'sheet', 'xlsx', 'csv']:
                    type_filters.append("mimeType='application/vnd.google-apps.spreadsheet'")
                    # Also include Excel files
                    type_filters.append("mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'")
                    type_filters.append("mimeType='application/vnd.ms-excel'")
                elif ft_lower in ['pdf']:
                    type_filters.append("mimeType='application/pdf'")
                elif ft_lower in ['image', 'picture', 'photo', 'jpg', 'png', 'gif']:
                    type_filters.append("mimeType contains 'image/'")
                elif ft_lower in ['presentation', 'powerpoint', 'slides', 'ppt', 'pptx']:
                    type_filters.append("mimeType='application/vnd.google-apps.presentation'")
                    type_filters.append("mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'")
                elif ft_lower in ['document', 'doc', 'word', 'txt']:
                    type_filters.append("mimeType='application/vnd.google-apps.document'")
                    type_filters.append("mimeType='application/msword'")
                    type_filters.append("mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'")
                else:
                    # Default: search by mimeType
                    type_filters.append(f"mimeType contains '{ft_lower}'")
            
            if type_filters:
                q_parts.append(f"({' or '.join(type_filters)})")
        
        # Build date filters
        if created_after:
            q_parts.append(f"createdTime > '{created_after.isoformat()}'")
        if modified_after:
            q_parts.append(f"modifiedTime > '{modified_after.isoformat()}'")
        
        # Combine all filters
        full_query = " and ".join(q_parts)
        print(f"🔍 Search query: {full_query}")
        
        # Execute search
        try:
            results = self.service.files().list(
                q=full_query,
                spaces='drive',
                fields='files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)',
                pageSize=max_results
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
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