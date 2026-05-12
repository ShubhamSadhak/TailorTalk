import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pickle

class GoogleDriveService:
    def __init__(self, credentials_path: str, scopes: List[str]):
        self.credentials_path = credentials_path
        self.scopes = scopes
        self.service = None
        self.creds = None
        
    def authenticate(self):
        """Authenticate and build the Drive service"""
        token_path = 'token.pickle'
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes
                )
                self.creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('drive', 'v3', credentials=self.creds)
        return self.service
    
    def search_files(
        self,
        query: str = "",
        file_types: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        modified_after: Optional[datetime] = None,
        max_results: int = 50
    ) -> List[Dict]:
        """Search files in Google Drive"""
        drive_query_parts = []
        
        # Add name search
        if query:
            drive_query_parts.append(f"name contains '{query}'")
        
        # Add file type filters
        if file_types:
            type_queries = []
            for ft in file_types:
                if ft.lower() == 'pdf':
                    type_queries.append("mimeType='application/pdf'")
                elif ft.lower() == 'document':
                    type_queries.append("mimeType='application/vnd.google-apps.document'")
                elif ft.lower() == 'spreadsheet':
                    type_queries.append("mimeType='application/vnd.google-apps.spreadsheet'")
                elif ft.lower() == 'presentation':
                    type_queries.append("mimeType='application/vnd.google-apps.presentation'")
                elif ft.lower() == 'image':
                    type_queries.append("mimeType contains 'image/'")
            if type_queries:
                drive_query_parts.append(f"({' or '.join(type_queries)})")
        
        # Add date filters
        if created_after:
            drive_query_parts.append(f"createdTime > '{created_after.isoformat()}'")
        if modified_after:
            drive_query_parts.append(f"modifiedTime > '{modified_after.isoformat()}'")
        
        # Combine all query parts
        full_query = " and ".join(drive_query_parts) if drive_query_parts else ""
        
        # Execute search
        results = []
        page_token = None
        
        while len(results) < max_results:
            response = self.service.files().list(
                q=full_query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)',
                pageToken=page_token,
                pageSize=min(100, max_results - len(results))
            ).execute()
            
            results.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
        
        return results[:max_results]
    
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
        """Get recently modified files"""
        modified_after = datetime.now() - timedelta(days=days)
        return self.search_files(modified_after=modified_after, max_results=max_results)