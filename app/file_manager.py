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