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
            
            # Method 1: Try to get credentials from environment variable (Render.com)
            creds_json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if creds_json_str:
                try:
                    print("📖 Loading credentials from GOOGLE_CREDENTIALS_JSON environment variable")
                    # Clean and parse the JSON
                    creds_json_str = creds_json_str.strip()
                    creds_dict = json.loads(creds_json_str)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict,
                        scopes=['https://www.googleapis.com/auth/drive.readonly']
                    )
                    print("✅ Successfully loaded credentials from environment variable")
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse GOOGLE_CREDENTIALS_JSON: {e}")
                except Exception as e:
                    print(f"❌ Error loading credentials from env: {e}")
            
            # Method 2: Try to load from file
            if not credentials and self.service_account_file and os.path.exists(self.service_account_file):
                try:
                    print(f"📖 Loading credentials from file: {self.service_account_file}")
                    credentials = service_account.Credentials.from_service_account_file(
                        self.service_account_file,
                        scopes=['https://www.googleapis.com/auth/drive.readonly']
                    )
                    print("✅ Successfully loaded credentials from file")
                except Exception as e:
                    print(f"❌ Failed to load from file: {e}")
            
            if not credentials:
                raise Exception("No valid credentials found. Set GOOGLE_CREDENTIALS_JSON environment variable or provide a valid service account file.")
            
            self.service = build('drive', 'v3', credentials=credentials)
            return self.service
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
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
            raise Exception("DRIVE_FOLDER_ID is not set. Please configure it in environment variables.")
        
        # Build the folder filter (ALWAYS include this)
        q_parts = [f"'{self.folder_id}' in parents"]
        
        # Build name filter (partial match)
        if query:
            # Escape single quotes in the query
            safe_query = query.replace("'", "\\'")
            q_parts.append(f"name contains '{safe_query}'")
        
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
        print(f"🔍 Search query: {full_query}")
        
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