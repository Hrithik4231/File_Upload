import streamlit as st
import json
import os
import datetime
import uuid
from pathlib import Path
import fitz  # PyMuPDF
import base64
from typing import List, Dict, Tuple, Optional
import re
import time
from app.file_manager import FileManager
class UploadDocumentUI:
    """Class for handling document upload interface"""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
    
    def run(self):
        """Main method to run the upload interface"""
        st.header("📤 Upload Document")
        st.write("Upload PDF files to analyze and chat with them.")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Maximum file size: 5MB"
        )
        
        if uploaded_file is not None:
            # Validate file size (5MB limit)
            if uploaded_file.size > 5 * 1024 * 1024:
                st.error("File size exceeds 5MB limit. Please choose a smaller file.")
                return
            
            # Check if file already exists
            existing_metadata = self.file_manager.load_metadata()
            existing_files = [meta['filename'] for meta in existing_metadata.values()]
            
            if uploaded_file.name in existing_files:
                st.warning(f"File '{uploaded_file.name}' already exists!")
                return
            
            # Upload button
            if st.button("Upload File", type="primary"):
                with st.spinner("Uploading file..."):
                    try:
                        # Create file ID and add metadata
                        file_id = self.file_manager.add_file_metadata(
                            uploaded_file.name,
                            uploaded_file.size
                        )
                        
                        # Save file
                        file_path = self.file_manager.uploads_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Update status to processing
                        self.file_manager.update_file_status(file_id, 'processing')
                        
                        # Simulate processing time
                        time.sleep(1)
                        
                        # Update status to success
                        self.file_manager.update_file_status(file_id, 'success')
                        
                        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
                        st.balloons()
                        
                        # Display file info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("File Name", uploaded_file.name)
                        with col2:
                            st.metric("File Size", self.file_manager.format_file_size(uploaded_file.size))
                        with col3:
                            st.metric("Status", "Ready")
                        
                    except Exception as e:
                        st.error(f"Error uploading file: {str(e)}")
                        # Clean up on error
                        if 'file_id' in locals():
                            self.file_manager.delete_file(file_id)