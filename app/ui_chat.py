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



# import streamlit as st
# from google.generativeai.generative_models import GenerativeModel
# from typing import List, Dict, Optional
# import time

# class ChatWithPDFUI:
#     """Chat UI that uses ChromaDB for document retrieval"""
    
#     def __init__(self, file_manager, chat_sidebar, chat_memory):
#         self.file_manager = file_manager
#         self.chat_sidebar = chat_sidebar
#         self.chat_memory = chat_memory
        
#         # Configure Gemini API (you'll need to set this up)
#         # genai.configure(api_key="YOUR_API_KEY")  # Replace with your API key
#         self.model = None
#         try:
#             self.model = GenerativeModel('gemini-pro')
#         except Exception as e:
#             st.error(f"Error initializing Gemini model: {str(e)}")
    
#     def run(self):
#         st.header("💬 Chat with PDF")
        
#         # Check if switched from view uploads
#         if st.session_state.get('switch_to_chat', False):
#             st.session_state.switch_to_chat = False
        
#         # Get available files
#         metadata = self.file_manager.load_metadata()
        
#         if not metadata:
#             st.info("📝 No documents found. Upload a document first to start chatting!")
#             if st.button("📤 Go to Upload"):
#                 st.session_state.current_tab = "upload"
#                 st.rerun()
#             return
        
#         # File selection (if not already selected)
#         selected_file_id = st.session_state.get('selected_pdf_id')
        
#         if not selected_file_id or selected_file_id not in metadata:
#             st.markdown("### 📋 Select a Document")
#             self._display_file_selection(metadata)
#             return
        
#         # Display selected file info
#         selected_file = metadata[selected_file_id]
#         self._display_selected_file_info(selected_file_id, selected_file)
        
#         # Chat interface
#         self._display_chat_interface(selected_file_id, selected_file)
    
#     def _display_file_selection(self, metadata):
#         """Display file selection interface"""
#         st.markdown("Choose a document to start chatting:")
        
#         # Create columns for file cards
#         files_per_row = 2
#         file_items = list(metadata.items())
        
#         for i in range(0, len(file_items), files_per_row):
#             cols = st.columns(files_per_row)
            
#             for j, (file_id, file_info) in enumerate(file_items[i:i+files_per_row]):
#                 with cols[j]:
#                     with st.container():
#                         st.markdown(f"**📄 {file_info['filename']}**")
#                         st.caption(f"Size: {self.file_manager.format_file_size(file_info['filesize'])}")
#                         st.caption(f"Chunks: {file_info.get('chunk_count', 0)}")
#                         st.caption(f"Uploaded: {self.file_manager.format_datetime(file_info['created_at'])}")
                        
#                         if st.button("💬 Chat with this file", key=f"select_{file_id}"):
#                             st.session_state.selected_pdf_id = file_id
#                             st.rerun()
    
#     def _display_selected_file_info(self, file_id, file_info):
#         """Display information about the selected file"""
#         col1, col2, col3 = st.columns([2, 1, 1])
        
#         with col1:
#             st.markdown(f"**📄 Chatting with:** {file_info['filename']}")
        
#         with col2:
#             st.markdown(f"**📊 Chunks:** {file_info.get('chunk_count', 0)}")
        
#         with col3:
#             if st.button("🔄 Change File"):
#                 st.session_state.selected_pdf_id = None
#                 st.rerun()
        
#         st.markdown("---")
    
#     def _display_chat_interface(self, file_id, file_info):
#         """Display the chat interface"""
#         # Get or create current thread
#         current_thread_id = st.session_state.get('current_thread_id')
        
#         # If no thread selected, show thread management
#         if not current_thread_id:
#             self._display_thread_management(file_id, file_info['filename'])
#             return
        
#         # Display current thread messages
#         self._display_thread_messages(current_thread_id)
        
#         # Chat input
#         self._display_chat_input(current_thread_id, file_id, file_info['filename'])
    
#     def _display_thread_management(self, file_id, filename):
#         """Display thread management interface"""
#         st.markdown("### 💭 Chat Threads")
        
#         # Get existing threads for this file
#         threads = self.chat_memory.get_threads_for_pdf(file_id)
        
#         if threads:
#             st.markdown("**Existing Conversations:**")
#             for thread in threads[:5]:  # Show last 5 threads
#                 col1, col2 = st.columns([3, 1])
                
#                 with col1:
#                     thread_title = thread.get('title', 'Untitled')
#                     message_count = thread.get('message_count', 0)
#                     updated_at = self.chat_memory.format_datetime(thread.get('updated_at'))
                    
#                     st.markdown(f"**{thread_title}**")
#                     st.caption(f"{message_count} messages • {updated_at}")
                
#                 with col2:
#                     if st.button("Continue", key=f"continue_{thread['thread_id']}"):
#                         st.session_state.current_thread_id = thread['thread_id']
#                         st.rerun()
        
#         # Start new conversation
#         st.markdown("**Start New Conversation:**")
#         with st.form("new_chat_form"):
#             question = st.text_area(
#                 "What would you like to ask about this document?",
#                 placeholder="e.g., What is this document about? Summarize the main points...",
#                 height=100
#             )
            
#             if st.form_submit_button("🚀 Start Conversation", type="primary"):
#                 if question.strip():
#                     # Create new thread
#                     thread_id = self.chat_memory.create_new_thread(file_id, filename, question)
#                     st.session_state.current_thread_id = thread_id
                    
#                     # Process the first question
#                     self._process_question(thread_id, file_id, question)
#                     st.rerun()
#                 else:
#                     st.error("Please enter a question to start the conversation.")
    
#     def _display_thread_messages(self, thread_id):
#         """Display messages in the current thread"""
#         messages = self.chat_memory.load_thread_messages(thread_id)
        
#         if not messages:
#             st.info("No messages in this conversation yet.")
#             return
        
#         # Display messages
#         for message in messages:
#             # User question
#             with st.chat_message("user"):
#                 st.write(message['question'])
            
#             # Assistant response
#             with st.chat_message("assistant"):
#                 st.write(message['answer'])
                
#                 # Display sources if available
#                 sources = message.get('sources', [])
#                 if sources:
#                     with st.expander(f"📚 Sources ({len(sources)} references)", expanded=False):
#                         for i, source in enumerate(sources):
#                             st.markdown(f"**Source {i+1}** (Page {source['page_number']}):")
#                             st.text_area(
#                                 f"Content from {source['filename']}",
#                                 source['content'][:300] + ("..." if len(source['content']) > 300 else ""),
#                                 height=80,
#                                 key=f"source_{thread_id}_{i}_{message['timestamp']}"
#                             )
    
#     def _display_chat_input(self, thread_id, file_id, filename):
#         """Display chat input for asking questions"""
#         st.markdown("---")
        
#         # Chat input form
#         with st.form("chat_form", clear_on_submit=True):
#             col1, col2 = st.columns([4, 1])
            
#             with col1:
#                 question = st.text_input(
#                     "Ask a question about the document:",
#                     placeholder="What would you like to know?",
#                     key="chat_input"
#                 )
            
#             with col2:
#                 submit_button = st.form_submit_button("Send 🚀", type="primary")
            
#             if submit_button and question.strip():
#                 self._process_question(thread_id, file_id, question)
#                 st.rerun()
        
#         # Quick action buttons
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             if st.button("📝 Summarize Document"):
#                 self._process_question(thread_id, file_id, "Please provide a comprehensive summary of this document.")
#                 st.rerun()
        
#         with col2:
#             if st.button("🔑 Key Points"):
#                 self._process_question(thread_id, file_id, "What are the key points and main takeaways from this document?")
#                 st.rerun()
        
#         with col3:
#             if st.button("❓ Ask Anything"):
#                 question = st.text_input("Custom question:", key="custom_question")
#                 if question:
#                     self._process_question(thread_id, file_id, question)
#                     st.rerun()
    
#     def _process_question(self, thread_id, file_id, question):
#         """Process a user question and generate response"""
#         with st.spinner("🤔 Thinking..."):
#             try:
#                 # Step 1: Query similar documents from ChromaDB
#                 relevant_sources = self.file_manager.query_documents(
#                     query=question,
#                     file_id=file_id,
#                     n_results=5
#                 )
                
#                 if not relevant_sources:
#                     st.error("No relevant content found in the document.")
#                     return
                
#                 # Step 2: Prepare context for LLM
#                 context = self._prepare_context(relevant_sources, question)
                
#                 # Step 3: Generate response using Gemini
#                 response = self._generate_response(context, question)
                
#                 # Step 4: Save to thread
#                 self.chat_memory.add_message_to_thread(
#                     thread_id=thread_id,
#                     question=question,
#                     answer=response,
#                     sources=relevant_sources
#                 )
                
#                 st.success("✅ Response generated successfully!")
                
#             except Exception as e:
#                 st.error(f"Error processing question: {str(e)}")
    
#     def _prepare_context(self, sources, question):
#         """Prepare context from relevant sources"""
#         context_parts = []
        
#         for i, source in enumerate(sources):
#             context_parts.append(
#                 f"Source {i+1} (Page {source['page_number']}):\n{source['content']}\n"
#             )
        
#         context = "\n".join(context_parts)
        
#         prompt = f"""
#         Based on the following context from the document, please answer the user's question.
        
#         Context:
#         {context}
        
#         Question: {question}
        
#         Instructions:
#         - Provide a comprehensive and accurate answer based on the context
#         - If the context doesn't contain enough information, say so clearly
#         - Reference specific parts of the document when relevant
#         - Be concise but thorough
        
#         Answer:
#         """
        
#         return prompt
    
#     def _generate_response(self, context, question):
#         """Generate response using Gemini API"""
#         try:
#             if not self.model:
#                 return "Sorry, the AI model is not available. Please check your API configuration."
            
#             response = self.model.generate_content(context)
#             return response.text
            
#         except Exception as e:
#             st.error(f"Error generating response: {str(e)}")
#             return f"I apologize, but I encountered an error while processing your question: {str(e)}"
    
#     def _display_thread_controls(self, thread_id):
#         """Display thread control buttons"""
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             if st.button("🔄 New Thread"):
#                 st.session_state.current_thread_id = None
#                 st.rerun()
        
#         with col2:
#             if st.button("📋 Thread History"):
#                 # Show thread management
#                 st.session_state.show_thread_history = True
#                 st.rerun()
        
#         with col3:
#             if st.button("🗑️ Delete Thread"):
#                 if self.chat_memory.delete_thread(thread_id):
#                     st.session_state.current_thread_id = None
#                     st.success("Thread deleted successfully!")
#                     st.rerun()