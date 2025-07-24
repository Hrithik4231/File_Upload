import streamlit as st
import json
import os
import datetime
import uuid
from pathlib import Path
# import fitz  # PyMuPDF
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


# import streamlit as st
# from typing import Optional
# import time

# class UploadDocumentUI:
#     """Upload UI that works with ChromaDB storage"""
    
#     def __init__(self, file_manager):
#         self.file_manager = file_manager
    
#     def run(self):
#         st.header("📤 Upload Document")
#         st.markdown("Upload PDF or text files to add them to your vector database.")
        
#         # File upload widget
#         uploaded_file = st.file_uploader(
#             "Choose a file",
#             type=['pdf', 'txt'],
#             help="Supported formats: PDF, TXT"
#         )
        
#         if uploaded_file is not None:
#             # Display file info
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Filename", uploaded_file.name)
#             with col2:
#                 st.metric("Size", self.file_manager.format_file_size(uploaded_file.size))
#             with col3:
#                 file_type = "PDF" if uploaded_file.name.lower().endswith('.pdf') else "Text"
#                 st.metric("Type", file_type)
            
#             # Read file content
#             file_content = uploaded_file.read()
            
#             # Check if file already exists
#             existing_id = self.file_manager.file_exists_in_db(file_content, uploaded_file.name)
            
#             if existing_id:
#                 st.warning(f"⚠️ File '{uploaded_file.name}' already exists in the database!")
#                 file_info = self.file_manager.get_file_info(existing_id)
#                 if file_info:
#                     st.info(f"📅 Originally uploaded: {self.file_manager.format_datetime(file_info['created_at'])}")
#                     st.info(f"📊 Contains {file_info.get('chunk_count', 0)} text chunks")
#             else:
#                 # Upload button
#                 if st.button("🚀 Upload and Process", type="primary"):
#                     self._process_upload(uploaded_file.name, uploaded_file.size, file_content)
        
#         # Display recent uploads
#         self._display_recent_uploads()
    
#     def _process_upload(self, filename: str, filesize: int, file_content: bytes):
#         """Process file upload with progress tracking"""
        
#         # Create progress bar and status
#         progress_bar = st.progress(0)
#         status_text = st.empty()
        
#         try:
#             # Step 1: Initial processing
#             status_text.text("🔄 Initializing upload...")
#             progress_bar.progress(10)
#             time.sleep(0.5)
            
#             # Step 2: Add to ChromaDB
#             status_text.text("📊 Processing and embedding document...")
#             progress_bar.progress(30)
            
#             file_id = self.file_manager.add_file_metadata(filename, filesize, file_content)
#             progress_bar.progress(70)
            
#             # Step 3: Finalizing
#             status_text.text("✅ Finalizing upload...")
#             progress_bar.progress(90)
#             time.sleep(0.5)
            
#             # Step 4: Complete
#             progress_bar.progress(100)
#             status_text.text("🎉 Upload completed successfully!")
            
#             # Show success message
#             st.success(f"✅ '{filename}' has been successfully uploaded and processed!")
            
#             # Get file info to show statistics
#             file_info = self.file_manager.get_file_info(file_id)
#             if file_info:
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     st.info(f"📝 File ID: `{file_id}`")
#                 with col2:
#                     st.info(f"🔢 Text chunks created: {file_info.get('chunk_count', 0)}")
            
#             # Clear the progress indicators after a moment
#             time.sleep(2)
#             progress_bar.empty()
#             status_text.empty()
            
#         except Exception as e:
#             progress_bar.empty()
#             status_text.empty()
#             st.error(f"❌ Error uploading file: {str(e)}")
#             st.error("Please try again or contact support if the problem persists.")
    
#     def _display_recent_uploads(self):
#         """Display recently uploaded files"""
#         st.markdown("---")
#         st.subheader("📋 Recent Uploads")
        
#         metadata = self.file_manager.load_metadata()
        
#         if not metadata:
#             st.info("No files uploaded yet. Upload your first document above!")
#             return
        
#         # Sort by upload date (most recent first)
#         sorted_files = sorted(
#             metadata.items(), 
#             key=lambda x: x[1].get('created_at', ''), 
#             reverse=True
#         )
        
#         # Display recent files (limit to 5)
#         recent_files = sorted_files[:5]
        
#         for file_id, file_info in recent_files:
#             with st.container():
#                 col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
#                 with col1:
#                     st.write(f"📄 **{file_info['filename']}**")
#                     st.caption(f"Uploaded: {self.file_manager.format_datetime(file_info['created_at'])}")
                
#                 with col2:
#                     st.write(self.file_manager.format_file_size(file_info['filesize']))
                
#                 with col3:
#                     chunk_count = file_info.get('chunk_count', 0)
#                     st.write(f"{chunk_count} chunks")
                
#                 with col4:
#                     file_type = file_info.get('file_type', 'unknown').upper()
#                     if file_type == 'PDF':
#                         st.write("📄 PDF")
#                     else:
#                         st.write("📝 TXT")
                
#                 st.divider()
        
#         # Show database statistics
#         stats = self.file_manager.get_database_stats()
        
#         st.markdown("### 📊 Database Statistics")
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric("Total Files", stats['total_files'])
#         with col2:
#             st.metric("Text Chunks", stats['total_chunks'])
#         with col3:
#             st.metric("Chat Threads", stats['total_threads'])
#         with col4:
#             st.metric("Total Messages", stats['total_messages'])
        
#         # Link to view all uploads
#         if len(metadata) > 5:
#             st.info(f"Showing 5 most recent files. You have {len(metadata)} total files. Go to 'View Uploads' to see all files.")