import streamlit as st
import json
import datetime
import uuid
from pathlib import Path
from typing import List, Dict, Tuple, Optional


# Gemini API imports
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.client import configure

class FileManager:
    """Utility class for file and metadata management"""
    
    def __init__(self):
        self.uploads_dir = Path("uploads")
        self.metadata_file = self.uploads_dir / "file_data.json"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.uploads_dir.mkdir(exist_ok=True)
    
    def load_metadata(self) -> Dict:
        """Load metadata from JSON file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_metadata(self, metadata: Dict):
        """Save metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def add_file_metadata(self, filename: str, filesize: int, file_id: Optional[str] = None) -> str:
        """Add file metadata and return file ID"""
        if file_id is None:
            file_id = str(uuid.uuid4())
        
        metadata = self.load_metadata()
        metadata[file_id] = {
            'filename': filename,
            'filesize': filesize,
            'created_at': datetime.datetime.now(),
            'status': 'uploading',
            'file_id': file_id
        }
        self.save_metadata(metadata)
        return file_id
    
    def update_file_status(self, file_id: str, status: str):
        """Update file status"""
        metadata = self.load_metadata()
        if file_id in metadata:
            metadata[file_id]['status'] = status
            self.save_metadata(metadata)
    
    def delete_file(self, file_id: str):
        """Delete file and its metadata"""
        metadata = self.load_metadata()
        if file_id in metadata:
            filename = metadata[file_id]['filename']
            file_path = self.uploads_dir / filename
            
            # Delete physical file
            if file_path.exists():
                file_path.unlink()
            
            # Remove from metadata
            del metadata[file_id]
            self.save_metadata(metadata)
            return True
        return False
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """Get file path from file ID"""
        metadata = self.load_metadata()
        if file_id in metadata:
            filename = metadata[file_id]['filename']
            return self.uploads_dir / filename
        return None
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes = int(size_bytes / 1024)
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def format_datetime(dt) -> str:
        """Format datetime for display"""
        if isinstance(dt, str):
            try:
                dt = datetime.datetime.fromisoformat(dt)
            except:
                return dt
        return dt.strftime("%Y-%m-%d %H:%M:%S")


# import streamlit as st
# import datetime
# from pathlib import Path
# from typing import List, Dict, Tuple, Optional
# from .chromadb_manager import ChromaDBManager

# class FileManager:
#     """File manager that uses ChromaDB for storage instead of local files"""
    
#     def __init__(self):
#         self.chromadb = ChromaDBManager()
    
#     def load_metadata(self) -> Dict:
#         """Load all file metadata from ChromaDB"""
#         files = self.chromadb.get_all_files()
#         metadata = {}
        
#         for file_info in files:
#             file_id = file_info['file_id']
#             metadata[file_id] = {
#                 'filename': file_info['filename'],
#                 'filesize': file_info['filesize'],
#                 'created_at': self.parse_datetime(file_info['created_at']),
#                 'status': file_info.get('status', 'processed'),
#                 'file_id': file_id,
#                 'chunk_count': file_info.get('chunk_count', 0),
#                 'file_type': file_info.get('file_type', 'unknown')
#             }
        
#         return metadata
    
#     def save_metadata(self, metadata: Dict):
#         """This method is kept for compatibility but does nothing since ChromaDB handles persistence"""
#         pass
    
#     def add_file_metadata(self, filename: str, filesize: int, file_content: bytes, file_id: Optional[str] = None) -> str:
#         """Add file to ChromaDB and return file ID"""
#         try:
#             # Check if file already exists
#             existing_id = self.chromadb.file_exists(file_content, filename)
#             if existing_id:
#                 st.info(f"File '{filename}' already exists in database.")
#                 return existing_id
            
#             # Add file to ChromaDB
#             file_id = self.chromadb.add_file_to_chromadb(file_content, filename, filesize)
#             return file_id
            
#         except Exception as e:
#             st.error(f"Error adding file: {str(e)}")
#             raise e
    
#     def update_file_status(self, file_id: str, status: str):
#         """Update file status in ChromaDB"""
#         # Get current metadata
#         file_metadata = self.chromadb.get_file_metadata(file_id)
#         if file_metadata:
#             # ChromaDB doesn't support direct updates, but status is managed internally
#             pass
    
#     def delete_file(self, file_id: str) -> bool:
#         """Delete file from ChromaDB"""
#         return self.chromadb.delete_file(file_id)
    
#     def get_file_path(self, file_id: str) -> Optional[Path]:
#         """Get file path - returns None since files are stored in ChromaDB"""
#         # Files are no longer stored as physical files
#         return None
    
#     def file_exists_in_db(self, file_content: bytes, filename: str) -> Optional[str]:
#         """Check if file exists in ChromaDB"""
#         return self.chromadb.file_exists(file_content, filename)
    
#     def get_file_info(self, file_id: str) -> Optional[Dict]:
#         """Get file information from ChromaDB"""
#         return self.chromadb.get_file_metadata(file_id)
    
#     def query_documents(self, query: str, file_id: Optional[str] = None, n_results: int = 5) -> List[Dict]:
#         """Query documents using vector similarity"""
#         return self.chromadb.query_documents(query, file_id, n_results)
    
#     def get_database_stats(self) -> Dict:
#         """Get database statistics"""
#         return self.chromadb.get_database_stats()
    
#     @staticmethod
#     def format_file_size(size_bytes: int) -> str:
#         """Format file size in human readable format"""
#         for unit in ['B', 'KB', 'MB', 'GB']:
#             if size_bytes < 1024:
#                 return f"{size_bytes:.1f} {unit}"
#             size_bytes = int(size_bytes / 1024)
#         return f"{size_bytes:.1f} TB"
    
#     @staticmethod
#     def format_datetime(dt) -> str: 
#         """Format datetime for display"""
#         if isinstance(dt, str):
#             try:
#                 dt = datetime.datetime.fromisoformat(dt.replace('T', ' '))
#             except:
#                 return dt
#         elif not isinstance(dt, datetime.datetime):
#             return "Unknown"
        
#         return dt.strftime("%Y-%m-%d %H:%M:%S")
    
#     @staticmethod
#     def parse_datetime(dt):
#         """Parse datetime string to datetime object"""
#         if isinstance(dt, str):
#             try:
#                 return datetime.datetime.fromisoformat(dt.replace('T', ' '))
#             except:
#                 return datetime.datetime.now()
#         return dt