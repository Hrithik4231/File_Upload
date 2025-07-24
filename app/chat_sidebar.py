
import streamlit as st
from typing import Dict, List, Optional
from app.chat_memory import ChatMemoryManager
from app.file_manager import FileManager

class ChatSidebar:
    """Manages the chat history sidebar interface"""
    
    def __init__(self, file_manager: FileManager, chat_memory: ChatMemoryManager):
        self.file_manager = file_manager
        self.chat_memory = ChatMemoryManager()
        self.chat_memory = chat_memory
        
        # Initialize session state
        if 'current_thread_id' not in st.session_state:
            st.session_state.current_thread_id = None
        if 'sidebar_search_query' not in st.session_state:
            st.session_state.sidebar_search_query = ""
        if 'show_thread_options' not in st.session_state:
            st.session_state.show_thread_options = {}
        if 'pending_delete' not in st.session_state:
            st.session_state.pending_delete = {}
        if 'new_chat_mode' not in st.session_state:
            st.session_state.new_chat_mode = False
    
    def render_sidebar(self):
        """Render the complete sidebar with chat threads"""
        with st.sidebar:
            # Header
            st.markdown("### 💬 Chat History")
            
            # New Chat Button
            if st.button("➕ New Chat", use_container_width=True, type="primary"):
                self.start_new_chat()
            
            st.markdown("---")
            
            # Search functionality
            self.render_search_box()
            
            # Thread statistics
            self.render_thread_stats()
            
            # Thread list
            self.render_thread_list()
    
    def render_search_box(self):
        """Render search functionality"""
        search_query = st.text_input(
            "🔍 Search chats",
            value=st.session_state.sidebar_search_query,
            placeholder="Search by title or content...",
            key="sidebar_search_input"
        )
        
        if search_query != st.session_state.sidebar_search_query:
            st.session_state.sidebar_search_query = search_query
            st.rerun()
    
    def render_thread_stats(self):
        """Render thread statistics"""
        stats = self.chat_memory.get_thread_stats()
        
        if stats['total_threads'] > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Chats", stats['total_threads'])
            with col2:
                st.metric("Messages", stats['total_messages'])
    
    def render_thread_list(self):
        """Render the list of chat threads"""
        # Get threads (filtered by search if applicable)
        if st.session_state.sidebar_search_query:
            threads = self.chat_memory.search_threads(st.session_state.sidebar_search_query)
            if threads:
                st.markdown(f"**Search Results ({len(threads)}):**")
            else:
                st.info("No chats found matching your search.")
                return
        else:
            threads = self.chat_memory.load_threads_index()
        
        if not threads:
            st.info("No chat history yet. Start a new chat!")
            return
        
        # Render each thread
        for thread in threads:
            self.render_thread_item(thread)
    
    def render_thread_item(self, thread: Dict):
        """Render individual thread item"""
        thread_id = thread['thread_id']
        is_current = st.session_state.current_thread_id == thread_id
        
        # Create container for the thread item
        thread_container = st.container()
        
        with thread_container:
            # Thread selection button with styling
            button_style = "primary" if is_current else "secondary"
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Thread title (clickable)
                if st.button(
                    self.format_thread_title(thread),
                    key=f"thread_btn_{thread_id}",
                    help=f"PDF: {thread.get('pdf_filename', 'Unknown')}\nCreated: {self.chat_memory.format_datetime(thread.get('created_at'))}",
                    use_container_width=True,
                    type=button_style
                ):
                    self.load_thread(thread_id)
            
            with col2:
                # Options button (three dots)
                if st.button("⋮", key=f"options_btn_{thread_id}", help="Thread options"):
                    # Toggle options visibility
                    if thread_id in st.session_state.show_thread_options:
                        del st.session_state.show_thread_options[thread_id]
                    else:
                        st.session_state.show_thread_options[thread_id] = True
                    st.rerun()
            
            # Show options if toggled
            if st.session_state.show_thread_options.get(thread_id, False):
                self.render_thread_options(thread)
            
            # Thread metadata
            st.caption(f"📄 {thread.get('pdf_filename', 'Unknown')} • {thread.get('message_count', 0)} messages • {self.chat_memory.format_datetime(thread.get('updated_at'))}")
        
        st.markdown("---")
    
    def render_thread_options(self, thread: Dict):
        """Render thread options (rename, delete)"""
        thread_id = thread['thread_id']
        
        with st.expander("Thread Options", expanded=True):
            # Rename option
            st.markdown("**Rename Chat:**")
            
            # Create a unique key for the text input
            rename_key = f"rename_input_{thread_id}"
            
            # Initialize the input value if not exists
            if rename_key not in st.session_state:
                st.session_state[rename_key] = thread['title']
            
            new_title = st.text_input(
                "New title:",
                value=st.session_state[rename_key],
                key=rename_key,
                placeholder="Enter new chat title..."
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✏️ Rename", key=f"rename_btn_{thread_id}", use_container_width=True):
                    # Get the current value from the text input
                    current_input = st.session_state.get(rename_key, "").strip()
                    
                    if current_input and current_input != thread['title']:
                        success = self.chat_memory.update_thread_title(thread_id, current_input)
                        if success:
                            st.success("Chat renamed successfully!")
                            # Hide options panel
                            if thread_id in st.session_state.show_thread_options:
                                del st.session_state.show_thread_options[thread_id]
                            st.rerun()
                        else:
                            st.error("Failed to rename chat.")
                    elif not current_input:
                        st.warning("Please enter a valid title.")
                    else:
                        st.info("Title is the same as current.")
            
            with col2:
                # Delete button with confirmation
                delete_key = f"confirm_delete_{thread_id}"
                
                if thread_id not in st.session_state.pending_delete:
                    # First click: Show delete button
                    if st.button("🗑️ Delete", key=f"delete_btn_{thread_id}", use_container_width=True, type="secondary"):
                        st.session_state.pending_delete[thread_id] = True
                        st.rerun()
                else:
                    # Second click: Confirm deletion
                    if st.button("⚠️ Confirm", key=delete_key, type="secondary", use_container_width=True):
                        success = self.delete_thread_with_cleanup(thread_id)
                        if success:
                            st.success("Chat deleted!")
                            # Clean up session state
                            if thread_id in st.session_state.pending_delete:
                                del st.session_state.pending_delete[thread_id]
                            if thread_id in st.session_state.show_thread_options:
                                del st.session_state.show_thread_options[thread_id]
                            st.rerun()
                        else:
                            st.error("Failed to delete chat.")
                            if thread_id in st.session_state.pending_delete:
                                del st.session_state.pending_delete[thread_id]
    
    def delete_thread_with_cleanup(self, thread_id: str) -> bool:
        """Delete thread with proper session state cleanup"""
        try:
            # Delete from storage
            success = self.chat_memory.delete_thread(thread_id)
            
            if success:
                # Clear current thread if it was deleted
                if st.session_state.current_thread_id == thread_id:
                    st.session_state.current_thread_id = None
                    # Clear associated chat history
                    thread = self.chat_memory.get_thread_by_id(thread_id)
                    if thread and 'chat_history' in st.session_state:
                        pdf_id = thread.get('pdf_file_id')
                        if pdf_id in st.session_state.chat_history:
                            st.session_state.chat_history[pdf_id] = []
                
                return True
            return False
            
        except Exception as e:
            st.error(f"Error deleting thread: {str(e)}")
            return False
    
    def format_thread_title(self, thread: Dict) -> str:
        """Format thread title for display"""
        title = thread.get('title', 'Untitled Chat')
        max_length = 35
        
        if len(title) > max_length:
            return title[:max_length-3] + "..."
        return title
    
    def start_new_chat(self):
        """Start a new chat session with proper initialization"""
        # Clear current thread
        st.session_state.current_thread_id = None
        st.session_state.new_chat_mode = True
        
        # Clear any existing options
        st.session_state.show_thread_options = {}
        st.session_state.pending_delete = {}
        
        # Clear chat history if a PDF is selected
        if 'selected_pdf_id' in st.session_state and st.session_state.selected_pdf_id:
            pdf_id = st.session_state.selected_pdf_id
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = {}
            st.session_state.chat_history[pdf_id] = []
        
        st.success("Started new chat! Select a PDF and ask a question to begin.")
        st.rerun()
    
    def load_thread(self, thread_id: str):
        """Load a specific chat thread"""
        thread = self.chat_memory.get_thread_by_id(thread_id)
        
        if not thread:
            st.error("Thread not found!")
            return
        
        # Set current thread
        st.session_state.current_thread_id = thread_id
        
        # Clear new chat mode
        st.session_state.new_chat_mode = False
        
        # Load PDF context
        pdf_file_id = thread['pdf_file_id']
        st.session_state.selected_pdf_id = pdf_file_id
        
        # Load chat messages
        messages = self.chat_memory.load_thread_messages(thread_id)
        
        # Convert to the format expected by ui_chat.py
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = {}
        
        st.session_state.chat_history[pdf_file_id] = messages
        
        # Hide thread options
        st.session_state.show_thread_options = {}
        st.session_state.pending_delete = {}
        
        st.success(f"Loaded chat: {thread['title']}")
        st.rerun()

    def clear_current_thread(self):
        """ Clear the current thread from session state """
        if 'current_thread_id' in st.session_state:
            del st.session_state['current_thread_id']
    
    def get_current_thread_id(self) -> Optional[str]:
        """Get the current thread ID from session state"""
        return st.session_state.get('current_thread_id')
    
    def create_thread_for_first_question(self, pdf_file_id: str, pdf_filename: str, first_question: str) -> str:
        """Create a new thread for the first question in a conversation"""
        thread_id = self.chat_memory.create_new_thread(pdf_file_id, pdf_filename, first_question)
        st.session_state.current_thread_id = thread_id
        return thread_id
        
        # Clear new chat mode since we now have an active thread
        st.session_state.new_chat_mode = False
        
        return thread_id
    
    def add_message_to_current_thread(self, question: str, answer: str, sources: Optional[List[Dict]] = None):
        """Add a message to the currently active thread"""
        if 'current_thread_id' in st.session_state:
            self.chat_memory.add_message_to_thread(
                st.session_state.current_thread_id,
                question,
                answer,
                sources
            )
    
    def is_new_conversation(self, pdf_file_id: str) -> bool:
        """Check if this is a new conversation (no current thread or different PDF)"""
        current_thread_id = self.get_current_thread_id()
        if not current_thread_id:
            return True
        thread = self.chat_memory.get_thread_by_id(current_thread_id)
        if not thread or thread.get('pdf_file_id') != pdf_file_id:
            return True
        return False
    

# import streamlit as st
# from typing import Dict, List, Optional

# class ChatSidebar:
#     """Chat sidebar that manages file selection and thread navigation with ChromaDB"""
    
#     def __init__(self, file_manager, chat_memory):
#         self.file_manager = file_manager
#         self.chat_memory = chat_memory
    
#     def render_sidebar(self):
#         """Render the chat sidebar"""
#         st.subheader("💬 Chat Controls")
        
#         # File selection section
#         self._render_file_selection()
        
#         st.markdown("---")
        
#         # Thread management section
#         selected_file_id = st.session_state.get('selected_pdf_id')
#         if selected_file_id:
#             self._render_thread_management(selected_file_id)
        
#         st.markdown("---")
        
#         # Quick stats
#         self._render_quick_stats()
    
#     def _render_file_selection(self):
#         """Render file selection dropdown"""
#         st.markdown("### 📄 Select Document")
        
#         # Get all files
#         metadata = self.file_manager.load_metadata()
        
#         if not metadata:
#             st.info("No documents available. Upload a document first!")
#             return
        
#         # Create options for selectbox
#         file_options = {}
#         file_labels = []
        
#         for file_id, file_info in metadata.items():
#             label = f"📄 {file_info['filename']}"
#             file_options[label] = file_id
#             file_labels.append(label)
        
#         # Current selection
#         current_file_id = st.session_state.get('selected_pdf_id')
#         current_index = 0
        
#         if current_file_id and current_file_id in metadata:
#             current_filename = metadata[current_file_id]['filename']
#             current_label = f"📄 {current_filename}"
#             if current_label in file_labels:
#                 current_index = file_labels.index(current_label)
        
#         # File selection
#         selected_label = st.selectbox(
#             "Choose a document:",
#             file_labels,
#             index=current_index,
#             key="file_selector"
#         )
        
#         selected_file_id = file_options[selected_label]
        
#         # Update session state if selection changed
#         if st.session_state.get('selected_pdf_id') != selected_file_id:
#             st.session_state.selected_pdf_id = selected_file_id
#             st.session_state.current_thread_id = None  # Reset thread selection
#             st.rerun()
        
#         # Display file info
#         if selected_file_id in metadata:
#             file_info = metadata[selected_file_id]
#             st.caption(f"📊 {file_info.get('chunk_count', 0)} chunks")
#             st.caption(f"📅 {self.file_manager.format_datetime(file_info['created_at'])}")
    
#     def _render_thread_management(self, file_id):
#         """Render thread management section"""
#         st.markdown("### 💭 Chat Threads")
        
#         # Get threads for selected file
#         threads = self.chat_memory.get_threads_for_pdf(file_id)
        
#         if not threads:
#             st.info("No conversations yet. Start chatting to create threads!")
#             return
        
#         # Current thread selection
#         current_thread_id = st.session_state.get('current_thread_id')
        
#         # Create thread options
#         thread_options = {}
#         thread_labels = ["➕ Start New Thread"]
#         thread_options[thread_labels[0]] = None
        
#         for thread in threads:
#             title = thread.get('title', 'Untitled')[:30]
#             if len(thread.get('title', '')) > 30:
#                 title += "..."
            
#             msg_count = thread.get('message_count', 0)
#             label = f"💬 {title} ({msg_count} msgs)"
#             thread_options[label] = thread['thread_id']
#             thread_labels.append(label)
        
#         # Find current selection index
#         current_index = 0
#         if current_thread_id:
#             for i, (label, thread_id) in enumerate(thread_options.items()):
#                 if thread_id == current_thread_id:
#                     current_index = i
#                     break
        
#         # Thread selection
#         selected_label = st.selectbox(
#             "Select conversation:",
#             thread_labels,
#             index=current_index,
#             key="thread_selector"
#         )
        
#         selected_thread_id = thread_options[selected_label]
        
#         # Update session state if selection changed
#         if st.session_state.get('current_thread_id') != selected_thread_id:
#             st.session_state.current_thread_id = selected_thread_id
#             st.rerun()
        
#         # Display thread info
#         if selected_thread_id:
#             thread_info = next((t for t in threads if t['thread_id'] == selected_thread_id), None)
#             if thread_info:
#                 st.caption(f"📅 {self.chat_memory.format_datetime(thread_info.get('updated_at'))}")
                
#                 # Thread actions
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     if st.button("✏️ Rename", key="rename_thread"):
#                         self._handle_thread_rename(selected_thread_id, thread_info)
                
#                 with col2:
#                     if st.button("🗑️ Delete", key="delete_thread"):
#                         self._handle_thread_delete(selected_thread_id, thread_info)
    
#     def _handle_thread_rename(self, thread_id, thread_info):
#         """Handle thread renaming"""
#         with st.form("rename_thread_form"):
#             new_title = st.text_input(
#                 "New thread title:",
#                 value = (thread_info.get('title') or ''),
#                 max_chars = 100
#             )
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.form_submit_button("💾 Save"):
#                     if new_title is not None and new_title.strip():
#                         if self.chat_memory.update_thread_title(thread_id, new_title.strip()):
#                             st.success("✅ Thread renamed!")
#                             st.rerun()
#                         else:
#                             st.error("❌ Failed to rename thread")
#                     else:
#                         st.error("Please enter a valid title")
            
#             with col2:
#                 if st.form_submit_button("❌ Cancel"):
#                     st.rerun()
    
#     def _handle_thread_delete(self, thread_id, thread_info):
#         """Handle thread deletion"""
#         st.warning(f"⚠️ Delete '{thread_info.get('title', 'Untitled')}'?")
#         st.caption("This will permanently delete all messages in this thread.")
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("🗑️ Delete", key="confirm_delete_thread", type="primary"):
#                 if self.chat_memory.delete_thread(thread_id):
#                     st.success("✅ Thread deleted!")
#                     st.session_state.current_thread_id = None
#                     st.rerun()
#                 else:
#                     st.error("❌ Failed to delete thread")
        
#         with col2:
#             if st.button("↩️ Cancel", key="cancel_delete_thread"):
#                 st.rerun()
    
#     def _render_quick_stats(self):
#         """Render quick statistics"""
#         st.markdown("### 📊 Quick Stats")
        
#         # Get database stats
#         stats = self.file_manager.get_database_stats()
        
#         # Display metrics
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.metric("📄 Files", stats['total_files'])
#             st.metric("🧵 Threads", stats['total_threads'])
        
#         with col2:
#             st.metric("📝 Chunks", stats['total_chunks'])
#             st.metric("💬 Messages", stats['total_messages'])
        
#         # Current file stats
#         selected_file_id = st.session_state.get('selected_pdf_id')
#         if selected_file_id:
#             threads = self.chat_memory.get_threads_for_pdf(selected_file_id)
#             total_messages = sum(t.get('message_count', 0) for t in threads)
            
#             st.markdown("**Current Document:**")
#             st.caption(f"💭 {len(threads)} threads")
#             st.caption(f"💬 {total_messages} messages")
        
#         # Search functionality
#         st.markdown("### 🔍 Search Threads")
#         search_query = st.text_input(
#             "Search conversations:",
#             placeholder="Search by content...",
#             key="thread_search"
#         )
        
#         if search_query:
#             self._display_search_results(search_query)
    
#     def _display_search_results(self, query):
#         """Display search results"""
#         matching_threads = self.chat_memory.search_threads(query)
        
#         if matching_threads:
#             st.markdown(f"**Found {len(matching_threads)} matches:**")
            
#             for thread in matching_threads[:5]:  # Limit to 5 results
#                 title = thread.get('title', 'Untitled')[:25]
#                 if len(thread.get('title', '')) > 25:
#                     title += "..."
                
#                 if st.button(
#                     f"💬 {title}",
#                     key=f"search_result_{thread['thread_id']}",
#                     help=f"File: {thread.get('pdf_filename', 'Unknown')}"
#                 ):
#                     # Set the file and thread
#                     st.session_state.selected_pdf_id = thread['pdf_file_id']
#                     st.session_state.current_thread_id = thread['thread_id']
#                     st.rerun()
#         else:
#             st.caption("No matching threads found.")
    
#     def get_selected_file_id(self) -> Optional[str]:
#         """Get the currently selected file ID"""
#         return st.session_state.get('selected_pdf_id')
    
#     def get_selected_thread_id(self) -> Optional[str]:
#         """Get the currently selected thread ID"""
#         return st.session_state.get('current_thread_id')
    
#     def reset_selections(self):
#         """Reset file and thread selections"""
#         st.session_state.selected_pdf_id = None
#         st.session_state.current_thread_id = None