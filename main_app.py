# from app.file_manager import FileManager
# from app.ui_upload import UploadDocumentUI
# from app.ui_view import ViewUploadsUI
# from app.ui_chat import ChatWithPDFUI

# import streamlit as st

# class PDFSummarizerApp:
#     def __init__(self):
#         self.file_manager = FileManager()
#         self.upload_ui = UploadDocumentUI(self.file_manager)
#         self.view_ui = ViewUploadsUI(self.file_manager)
#         self.chat_ui = ChatWithPDFUI(self.file_manager)

#         st.set_page_config(
#             page_title="PDF Summarizer & Chat",
#             page_icon="📚",
#             layout="wide",
#             initial_sidebar_state="expanded"
#         )

#     def run(self):
#         st.title("📚 PDF Summarizer & Chat Application")
#         st.markdown("---")

#         with st.sidebar:
#             st.title("Navigation")
#             nav_option = st.radio(
#                 "Choose a section:",
#                 ["📤 Upload Document", "📁 View Uploads", "💬 Chat with PDF"],
#                 index=0
#             )

#             metadata = self.file_manager.load_metadata()
#             st.metric("Total Files", len(metadata))
#             if metadata:
#                 total_size = sum(info['filesize'] for info in metadata.values())
#                 st.metric("Total Storage", self.file_manager.format_file_size(total_size))

#         if nav_option == "📤 Upload Document":
#             self.upload_ui.run()
#         elif nav_option == "📁 View Uploads":
#             self.view_ui.run()
#         elif nav_option == "💬 Chat with PDF":
#             self.chat_ui.run()

# def main():
#     app = PDFSummarizerApp()
#     app.run()

# if __name__ == "__main__":
#     main()



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
