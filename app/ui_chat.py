import re

import streamlit as st
import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from app.pdf_processor import PDFProcessor
from app.gemini_helper import model
from app.file_manager import FileManager
from app.chat_memory import ChatMemoryManager


class ChatWithPDFUI:
    """Class for chatting with PDF documents with integrated thread management"""
    
    def __init__(self, file_manager: FileManager, chat_sidebar=None, chat_memory = None):
        self.file_manager = file_manager
        self.pdf_processor = PDFProcessor()
        self.chat_sidebar = chat_sidebar
        self.chat_memory = chat_memory
       
        
        # Initialize session state for chat
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = {}
        if 'selected_pdf_content' not in st.session_state:
            st.session_state.selected_pdf_content = None
        if 'selected_pdf_id' not in st.session_state:
            st.session_state.selected_pdf_id = None
        if 'new_chat_clicked' not in st.session_state:
            st.session_state.new_chat_clicked = False
    
    def run(self):
        """Main method to run the chat interface"""
        st.header("💬 Chat with PDF")
        
        metadata = self.file_manager.load_metadata()
        
        if not metadata:
            st.info("No documents available for chat. Please upload some PDFs first.")
            return
        
        # PDF selection (modified to work with thread system)
        self.pdf_selection_interface(metadata)
        
        # Chat interface
        if st.session_state.selected_pdf_id:
            if st.button("New Chat", key = "new_chat_button"):
                st.session_state.new_chat_clicked = True
                st.session_state.chat_history[st.session_state.selected_pdf_id] = []
                if self.chat_sidebar:
                    self.chat_sidebar.clear_current_thread()
                st.rerun()
        if st.session_state.selected_pdf_id and not st.session_state.new_chat_clicked:
            self.chat_interface()
    
    def pdf_selection_interface(self, metadata: Dict):
        """Interface for selecting PDF to chat with (modified for thread integration)"""
        st.subheader("Select a PDF Document")
        
        # Create options for selectbox
        pdf_options = {}
        for file_id, file_info in metadata.items():
            if file_info.get('status') == 'success':
                display_name = f"{file_info['filename']} ({self.file_manager.format_file_size(file_info['filesize'])})"
                pdf_options[display_name] = file_id
        
        if not pdf_options:
            st.warning("No successfully uploaded PDFs available.")
            return
        
        default_index = 0
        if st.session_state.selected_pdf_id:
            
            for i, (display_name, file_id) in enumerate(pdf_options.items()):
                if file_id == st.session_state.selected_pdf_id:
                    default_index = i
                    break
        
        selected_display = st.selectbox(
            "Choose a PDF to chat with:",
            options=list(pdf_options.keys()),
            index=default_index
        )
        
        if selected_display:
            selected_file_id = pdf_options[selected_display]
            

            if selected_file_id != st.session_state.selected_pdf_id:
                self.handle_pdf_change(selected_file_id, metadata)
                st.session_state.new_chat_clicked = False
            
            # Display current PDF info
            file_info = metadata[selected_file_id]
            
            # Show current thread info if available
            current_thread_id = None
            thread = None

            if self.chat_sidebar:
                current_thread_id = self.chat_sidebar.get_current_thread_id()
            
                if current_thread_id:
                    thread = self.chat_sidebar.chat_memory.get_thread_by_id(current_thread_id)
                if thread:
                    st.info(f"📖 Chat Thread: **{thread['title']}** | PDF: **{file_info['filename']}**")
                else:
                    st.info(f"📖 Currently chatting with: **{file_info['filename']}**")
            else:
                st.info(f"📖 Currently chatting with: **{file_info['filename']}**")
    
    def handle_pdf_change(self, selected_file_id: str, metadata: Dict):
        """Handle PDF change and thread management"""
        st.session_state.selected_pdf_id = selected_file_id
        st.session_state.new_chat_clicked = False
        
        with st.spinner("Loading PDF content..."):
            self.load_pdf_content(selected_file_id)
        
        # Check if we need to start a new conversation
        if self.chat_sidebar and self.chat_sidebar.is_new_conversation(selected_file_id):
            # This is a new conversation - clear current thread
            st.session_state.current_thread_id = None
            
            # Initialize empty chat history for this PDF
            st.session_state.chat_history[selected_file_id] = []
        else:
            # Load existing chat history if not already loaded
            if selected_file_id not in st.session_state.chat_history:
                st.session_state.chat_history[selected_file_id] = []
    
    def load_pdf_content(self, file_id: str):
        """Load and process PDF content"""
        file_path = self.file_manager.get_file_path(file_id)
        
        if file_path and file_path.exists():
            try:
                pages_content = self.pdf_processor.extract_text_with_pages(file_path)
                chunks = self.pdf_processor.create_pdf_chunks(pages_content)
                
                st.session_state.selected_pdf_content = {
                    'pages': pages_content,
                    'chunks': chunks,
                    'file_path': str(file_path)
                }
                
                st.success(f"✅ Loaded {len(pages_content)} pages from PDF")
                
            except Exception as e:
                st.error(f"Error loading PDF: {str(e)}")
                st.session_state.selected_pdf_content = None
        else:
            st.error("PDF file not found")
    
    def chat_interface(self):
        """Main chat interface with thread integration"""
        st.subheader("Ask Questions About Your PDF")
        
        file_id = st.session_state.selected_pdf_id
        
        # Initialize chat history for this PDF if not exists
        if file_id not in st.session_state.chat_history:
            st.session_state.chat_history[file_id] = []
        
        # Display chat history
        self.display_chat_history(file_id)
        
        # Chat input
        user_question = st.text_input(
            "Ask a question about the PDF:",
            placeholder="e.g., What is the main topic discussed in this document?",
            key=f"chat_input_{file_id}"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("Send", key=f"send_btn_{file_id}", type="primary"):
                if user_question.strip():
                    self.process_question(file_id, user_question)
                    st.rerun()


    
    def display_chat_history(self, file_id: str):
        """Display chat history for the selected PDF"""
        chat_history = st.session_state.chat_history.get(file_id, [])
        
        if chat_history:
            st.subheader("Chat History")
            
            for i, chat in enumerate(chat_history):
                # User question
                with st.chat_message("user"):
                    st.write(chat['question'])
                
                # AI response
                with st.chat_message("assistant"):
                    st.write(chat['answer'])
                    
                    def format_source_markdown(source: Dict, index: int) -> str:
                        filename = source.get("filename", "Unknown Document")
                        page_number = source.get("page_number", "N/A")
                        raw_content = source.get("content", "")

    # Clean up content:
                        cleaned = re.sub(r'\s+', ' ', raw_content)  # collapse newlines/tabs to single space
                        cleaned = cleaned.strip()

    # Optional: truncate smartly
                        if len(cleaned) > 300:
                            cleaned = cleaned[:297].rsplit(" ", 1)[0] + "..."

                        return f"""
---

📄 **Source {index+1}**  
📄 **Document:** *{filename}*  
📄 **Page Number:** {page_number}  
📝 **Excerpt:**  
> {cleaned}
"""
                    # Display sources
                    if chat.get('sources'):
                        with st.expander("📚 Sources that contributed to your Answer", expanded=False):
                            for j, source in enumerate(chat['sources']):
                                st.markdown(format_source_markdown(source, j), unsafe_allow_html=False)

                
                st.divider()
        else:
            st.info("No messages yet. Start by asking a question about your PDF!")
    
    def process_question(self, file_id: str, question: str):
        """Process user question and generate answer with sources (integrated with thread system)"""
        if not st.session_state.selected_pdf_content:
            st.error("PDF content not loaded")
            return
        
        with st.spinner("Generating answer..."):
            try:
                # Get relevant content and sources
                relevant_chunks, sources = self.find_relevant_content(question)
                
                if not relevant_chunks:
                    answer = "I couldn't find relevant information in the PDF to answer your question."
                    sources = []
                else:
                    # Generate answer using Gemini
                    answer = self.generate_answer_with_gemini(question, relevant_chunks)
                
                # Get filename for sources
                metadata = self.file_manager.load_metadata()
                filename = metadata[file_id]['filename']
                
                # Format sources with filename
                formatted_sources = []
                for source in sources:
                    formatted_sources.append({
                        'filename': filename,
                        'page_number': source['page_number'],
                        'content': source['content']
                    })
                
                # Create chat entry
                chat_entry = {
                    'question': question,
                    'answer': answer,
                    'sources': formatted_sources,
                    'timestamp': datetime.datetime.now()
                }
                
                # Handle thread management
                if self.chat_sidebar:
                    current_thread_id = self.chat_sidebar.get_current_thread_id()
                    
                    # Check if this is the first question in a new conversation
                    if not current_thread_id or st.session_state.new_chat_clicked:
                        # Create new thread with first question as title
                        thread_id = self.chat_sidebar.create_thread_for_first_question(
                            file_id, filename, question
                        )
                        # Clear existing history to start fresh
                        st.session_state.chat_history[file_id] = []
                        st.session_state.new_chat_clicked = False
                    
                    # Add message to current thread
                    self.chat_sidebar.add_message_to_current_thread(
                        question, answer, formatted_sources
                    )
                
                # Add to session chat history
                st.session_state.chat_history[file_id].append(chat_entry)
                
                st.success("✅ Answer generated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing question: {str(e)}")
    
    def find_relevant_content(self, question: str) -> Tuple[List[str], List[Dict]]:
        """Find relevant content chunks based on the question"""
        if not st.session_state.selected_pdf_content:
            return [], []
        
        chunks = st.session_state.selected_pdf_content['chunks']
        
        # Simple keyword-based relevance scoring (can be enhanced with embedding similarity)
        question_words = set(question.lower().split())
        relevant_chunks = []
        sources = []
        
        for chunk in chunks:
            content_words = set(chunk['content'].lower().split())
            overlap = len(question_words.intersection(content_words))
            
            if overlap > 0:  # Basic relevance check
                relevance_score = overlap / len(question_words)
                relevant_chunks.append({
                    'content': chunk['content'],
                    'page_number': chunk['page_number'],
                    'score': relevance_score
                })
        
        # Sort by relevance and take top 5 chunks
        relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
        top_chunks = relevant_chunks[:5]
        
        # Prepare content and sources
        content_texts = []
        for chunk in top_chunks:
            content_texts.append(chunk['content'])
            sources.append({
                'page_number': chunk['page_number'],
                'content': chunk['content']
            })
        
        return content_texts, sources
    
    def generate_answer_with_gemini(self, question: str, relevant_chunks: List[str]) -> str:
        """Generate answer using Gemini API"""
        try:
            # Combine relevant chunks
            context = "\n\n".join(relevant_chunks)
            
            # Create prompt
            prompt = f"""
            Based on the following PDF content, please answer the user's question. 
            If the answer is not available in the provided content, please say so.
            
            Context from PDF:
            {context}
            
            Question: {question}
            
            Please provide a comprehensive answer based only on the information provided in the context.
            """
            
            # Generate response
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Error generating answer: {str(e)}"