from app.file_manager import FileManager
from app.ui_upload import UploadDocumentUI
from app.ui_view import ViewUploadsUI
from app.ui_chat import ChatWithPDFUI
from app.chat_sidebar import ChatSidebar
from app.chat_memory import ChatMemoryManager

import streamlit as st

class PDFSummarizerApp:
    def __init__(self):
        self.file_manager = FileManager()
        self.upload_ui = UploadDocumentUI(self.file_manager)
        self.view_ui = ViewUploadsUI(self.file_manager)
        file_manager = FileManager()  
        self.chat_memory = ChatMemoryManager()  
        self.chat_sidebar = ChatSidebar(self.file_manager, self.chat_memory)  
        self.chat_ui = ChatWithPDFUI(self.file_manager, self.chat_sidebar, self.chat_memory)

        
        # Initialize chat sidebar first
        
        # Pass chat_sidebar to chat_ui for integration
        # self.chat_ui = ChatWithPDFUI(self.file_manager, self.chat_sidebar)

        st.set_page_config(
            page_title="PDF Summarizer & Chat",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def run(self):
        st.title("📚 PDF Summarizer & Chat Application")
        st.markdown("---")

        if 'selected_pdf_id' not in st.session_state:
            st.session_state.selected_pdf_id = None
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = {}


        # Main navigation in sidebar
        with st.sidebar:
            st.title("Navigation")
            nav_option = st.radio(
                "Choose a section:",
                ["📤 Upload Document", "📁 View Uploads", "💬 Chat with PDF"],
                index=2  # Default to Chat tab
            )

            # File statistics
            metadata = self.file_manager.load_metadata()
            st.metric("Total Files", len(metadata))
            if metadata:
                total_size = sum(info['filesize'] for info in metadata.values())
                st.metric("Total Storage", self.file_manager.format_file_size(total_size))
            
            st.markdown("---")
            
            # Render chat sidebar if in chat mode
            if nav_option == "💬 Chat with PDF":
                self.chat_sidebar.render_sidebar()

        # Main content area
        if nav_option == "📤 Upload Document":
            self.upload_ui.run()
        elif nav_option == "📁 View Uploads":
            self.view_ui.run()
        elif nav_option == "💬 Chat with PDF":
            self.chat_ui.run()

def main():
    app = PDFSummarizerApp()
    app.run()

if __name__ == "__main__":
    main()


# """
# Main application file for PDF Summarizer & Chat with ChromaDB integration
# """

# import streamlit as st
# import os
# from pathlib import Path

# # Import your application modules
# # from app.chromadb_manager import ChromaDBManager
# from app.file_manager import FileManager
# from app.chat_memory import ChatMemoryManager
# from app.chat_sidebar import ChatSidebar
# from app.ui_upload import UploadDocumentUI
# from app.ui_view import ViewUploadsUI
# from app.ui_chat import ChatWithPDFUI

# class PDFSummarizerApp:
#     def __init__(self):
#         # Initialize ChromaDB-based components
#         self.chromadb_manager = ChromaDBManager()
#         self.file_manager = FileManager()
#         self.chat_memory = ChatMemoryManager()
#         self.chat_sidebar = ChatSidebar(self.file_manager, self.chat_memory)
        
#         # Initialize UI components
#         self.upload_ui = UploadDocumentUI(self.file_manager)
#         self.view_ui = ViewUploadsUI(self.file_manager)
#         self.chat_ui = ChatWithPDFUI(self.file_manager, self.chat_sidebar, self.chat_memory)

#         # Configure Streamlit page
#         st.set_page_config(
#             page_title="PDF Summarizer & Chat with ChromaDB",
#             page_icon="📚",
#             layout="wide",
#             initial_sidebar_state="expanded"
#         )
        
#         # Initialize session state
#         self._initialize_session_state()
    
#     def _initialize_session_state(self):
#         """Initialize session state variables"""
#         if 'selected_pdf_id' not in st.session_state:
#             st.session_state.selected_pdf_id = None
#         if 'current_thread_id' not in st.session_state:
#             st.session_state.current_thread_id = None
#         if 'chat_history' not in st.session_state:
#             st.session_state.chat_history = {}
#         if 'current_tab' not in st.session_state:
#             st.session_state.current_tab = "chat"
#         if 'switch_to_chat' not in st.session_state:
#             st.session_state.switch_to_chat = False

#     def run(self):
#         """Main application runner"""
#         # App header
#         st.title("📚 PDF Summarizer & Chat Application")
#         st.markdown("*Powered by ChromaDB Vector Storage*")
#         st.markdown("---")

#         # Main navigation in sidebar
#         with st.sidebar:
#             st.title("Navigation")
            
#             # Navigation options
#             nav_options = ["💬 Chat with PDF", "📤 Upload Document", "📁 View Uploads"]
#             default_index = 0
            
#             # Set default based on session state
#             if st.session_state.get('current_tab') == "upload":
#                 default_index = 1
#             elif st.session_state.get('current_tab') == "view":
#                 default_index = 2
            
#             nav_option = st.radio(
#                 "Choose a section:",
#                 nav_options,
#                 index=default_index
#             )
            
#             # Update session state based on selection
#             if nav_option == "📤 Upload Document":
#                 st.session_state.current_tab = "upload"
#             elif nav_option == "📁 View Uploads":
#                 st.session_state.current_tab = "view"
#             else:
#                 st.session_state.current_tab = "chat"

#             # Database statistics
#             self._display_sidebar_stats()
            
#             st.markdown("---")
            
#             # Render chat sidebar if in chat mode
#             if nav_option == "💬 Chat with PDF":
#                 self.chat_sidebar.render_sidebar()
            
#             # ChromaDB status
#             self._display_chromadb_status()

#         # Main content area
#         try:
#             if nav_option == "📤 Upload Document":
#                 self.upload_ui.run()
#             elif nav_option == "📁 View Uploads":
#                 self.view_ui.run()
#             elif nav_option == "💬 Chat with PDF":
#                 self.chat_ui.run()
#         except Exception as e:
#             st.error(f"An error occurred: {str(e)}")
#             st.error("Please try refreshing the page or contact support if the issue persists.")
    
#     def _display_sidebar_stats(self):
#         """Display database statistics in sidebar"""
#         st.subheader("📊 Database Stats")
        
#         try:
#             stats = self.file_manager.get_database_stats()
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.metric("Files", stats['total_files'])
#                 st.metric("Threads", stats['total_threads'])
            
#             with col2:
#                 st.metric("Chunks", stats['total_chunks'])
#                 st.metric("Messages", stats['total_messages'])
            
#             # Storage info
#             metadata = self.file_manager.load_metadata()
#             if metadata:
#                 total_size = sum(info['filesize'] for info in metadata.values())
#                 st.caption(f"💾 Total: {self.file_manager.format_file_size(total_size)}")
        
#         except Exception as e:
#             st.error(f"Error loading stats: {str(e)}")
    
#     def _display_chromadb_status(self):
#         """Display ChromaDB connection status"""
#         st.markdown("### 🔗 ChromaDB Status")
        
#         try:
#             # Test ChromaDB connection
#             collections = [
#                 self.chromadb_manager.documents_collection,
#                 self.chromadb_manager.chat_collection,
#                 self.chromadb_manager.files_collection
#             ]
            
#             if all(collections):
#                 st.success("✅ Connected")
#                 st.caption("Vector database ready")
#             else:
#                 st.error("❌ Connection issue")
        
#         except Exception as e:
#             st.error("❌ ChromaDB Error")
#             st.caption(f"Error: {str(e)[:50]}...")
        
#         # Database maintenance
#         if st.button("🧹 Cleanup Orphaned Data"):
#             self._cleanup_database()
    
#     def _cleanup_database(self):
#         """Cleanup orphaned data in database"""
#         try:
#             with st.spinner("Cleaning up database..."):
#                 # Get valid file IDs
#                 metadata = self.file_manager.load_metadata()
#                 valid_file_ids = list(metadata.keys())
                
#                 # Cleanup orphaned threads
#                 deleted_count = self.chat_memory.cleanup_orphaned_threads(valid_file_ids)
                
#                 if deleted_count > 0:
#                     st.success(f"✅ Cleaned up {deleted_count} orphaned threads")
#                 else:
#                     st.info("✨ Database is already clean")
        
#         except Exception as e:
#             st.error(f"Error during cleanup: {str(e)}")

# def main():
#     """Main entry point"""
#     try:
#         # Check if required environment variables are set
#         # You might want to add API key validation here
        
#         # Initialize and run the app
#         app = PDFSummarizerApp()
#         app.run()
        
#     except Exception as e:
#         st.error("Failed to initialize application")
#         st.error(f"Error: {str(e)}")
#         st.markdown("### Troubleshooting:")
#         st.markdown("1. Ensure all required packages are installed")
#         st.markdown("2. Check ChromaDB permissions and storage location")
#         st.markdown("3. Verify your Gemini API key is configured")
#         st.code("pip install -r requirements.txt", language="bash")

# if __name__ == "__main__":
#     main()