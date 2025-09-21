#!/usr/bin/env python3
"""
Google Drive Client for document operations
Uses tokens from Chrome extension instead of doing its own OAuth flow
"""

import os
import io
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


# Scopes for Google Drive API
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',  # Read/write files created by app
    'https://www.googleapis.com/auth/drive.readonly',  # Read access to files
    'https://www.googleapis.com/auth/documents',  # Read/write Google Docs
    'https://www.googleapis.com/auth/drive'  # Full access (use with caution)
]


class GoogleDriveClient:
    """Client for interacting with Google Drive API using extension tokens"""
    
    def __init__(self, access_token: str):
        """
        Initialize Google Drive client with token from Chrome extension
        
        Args:
            access_token: OAuth2 access token from Chrome extension
        """
        self.service = None
        self.docs_service = None
        self._authenticate_with_token(access_token)
    
    def _authenticate_with_token(self, access_token: str):
        """Authenticate using token from Chrome extension"""
        try:
            # Create credentials from the access token
            creds = Credentials(token=access_token)
            
            # Build the services
            self.service = build('drive', 'v3', credentials=creds)
            self.docs_service = build('docs', 'v1', credentials=creds)
            
        except Exception as e:
            raise Exception(f"Authentication failed: {e}")

    def upload_file(self, file_path: str, name: Optional[str] = None, 
                    folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Uploads a file to Google Drive.
        
        Args:
            file_path: Path to the local file.
            name: Name of the file in Google Drive (defaults to local file name).
            folder_id: ID of the folder to upload to (optional).
            
        Returns:
            Dictionary with file metadata.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local file not found: {file_path}")
        
        file_name = name if name else os.path.basename(file_path)
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,createdTime,modifiedTime'
            ).execute()
            
            return file
        except HttpError as error:
            raise Exception(f"Upload failed: {error}")

    def create_document(self, title: str, content: str = "", 
                        folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new Google Docs document
        
        Args:
            title: Title of the document
            content: Initial content (optional)
            folder_id: ID of folder to create in (optional)
            
        Returns:
            Dictionary with document metadata
        """
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document'
        }

        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                fields='id,name,mimeType,createdTime,modifiedTime'
            ).execute()
            
            # Add content if provided
            if content:
                # For now, just create the document without content
                # Content can be added later using Google Docs API
                print(f"Note: Document created. Content addition requires Google Docs API.")
            
            return file
        except HttpError as error:
            raise Exception(f"Document creation failed: {error}")

    def read_file(self, file_id: str, download_path: Optional[str] = None) -> bytes:
        """
        Read/download a file from Google Drive
        
        Args:
            file_id: ID of the file to read.
            download_path: Optional path to save the file locally.
            
        Returns:
            File content as bytes.
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            if download_path:
                with open(download_path, 'wb') as f:
                    f.write(file_content.getvalue())
            
            return file_content.getvalue()
        except HttpError as error:
            raise Exception(f"File read failed: {error}")

    def read_document_text(self, file_id: str) -> str:
        """
        Read content of a Google Docs document as plain text.
        
        Args:
            file_id: ID of the document.
            
        Returns:
            Document content as a string.
        """
        try:
            # Use Google Docs API to read content
            document = self.docs_service.documents().get(documentId=file_id).execute()
            content = ""
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for run in element['paragraph'].get('elements', []):
                        if 'textRun' in run:
                            content += run['textRun']['content']
            return content
        except HttpError as error:
            raise Exception(f"Document read failed: {error}")

    def update_document_content(self, file_id: str, content: str) -> bool:
        """
        Update content of a Google Docs document
        
        Args:
            file_id: ID of the document
            content: New content
            
        Returns:
            True if successful
        """
        try:
            # Create a temporary file with the content
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Upload the content using the file path
            media = MediaFileUpload(temp_file_path, mimetype='text/plain')
            
            self.service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            return True
        except HttpError as error:
            raise Exception(f"Document update failed: {error}")

    def list_files(self, folder_id: Optional[str] = None, 
                   query: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List files in Google Drive
        
        Args:
            folder_id: ID of the folder to list files from (optional).
            query: Search query string (e.g., "name contains 'report'").
            limit: Maximum number of files to return.
            
        Returns:
            List of dictionaries with file metadata.
        """
        q = ""
        if folder_id:
            q += f"'{folder_id}' in parents"
        if query:
            if q: q += " and "
            q += query
        
        try:
            results = self.service.files().list(
                pageSize=limit,
                q=q,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            items = results.get('files', [])
            return items
        except HttpError as error:
            raise Exception(f"List files failed: {error}")

    def search_files(self, name: str, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for files by name.
        
        Args:
            name: Name of the file to search for.
            folder_id: Optional folder ID to limit search.
            
        Returns:
            List of dictionaries with file metadata.
        """
        query = f"name contains '{name}'"
        return self.list_files(folder_id=folder_id, query=query)

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: ID of the file to delete.
            
        Returns:
            True if successful.
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            raise Exception(f"Delete failed: {error}")

    def create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new folder in Google Drive.
        
        Args:
            name: Name of the folder
            parent_folder_id: ID of parent folder (optional)
            
        Returns:
            Dictionary with folder metadata
        """
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        try:
            folder = self.service.files().create(
                body=file_metadata,
                fields='id,name,mimeType,createdTime'
            ).execute()
            
            return folder
        except HttpError as error:
            raise Exception(f"Folder creation failed: {error}")
