import json
import datetime
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
import streamlit as st
from datetime import datetime

def parse_datetime(dt):
    if isinstance(dt, str):
        return datetime.fromisoformat(dt)
    return dt

class ChatMemoryManager:
    """Manages chat thread storage and retrieval"""
    
    def __init__(self):
        self.chat_threads_dir = Path("chat_threads")
        self.threads_index_file = self.chat_threads_dir / "threads_index.json"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.chat_threads_dir.mkdir(exist_ok=True)
    
    def load_threads_index(self) -> List[Dict]:
        """Load threads index from JSON file"""
        if self.threads_index_file.exists():
            try:
                with open(self.threads_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def save_threads_index(self, threads: List[Dict]):
        """Save threads index to JSON file"""
        # Sort threads by updated_at (most recent first)
        threads.sort(key=lambda x: parse_datetime(x["updated_at"]), reverse=True)
        
        with open(self.threads_index_file, 'w', encoding='utf-8') as f:
            json.dump(threads, f, indent=2, default=str, ensure_ascii=False)
    
    def create_new_thread(self, pdf_file_id: str, pdf_filename: str, first_question: str) -> str:
        """Create a new chat thread"""
        thread_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create thread metadata
        thread_data = {
            'thread_id': thread_id,
            'title': first_question[:50] + ('...' if len(first_question) > 50 else ''),
            'pdf_file_id': pdf_file_id,
            'pdf_filename': pdf_filename,
            'created_at': timestamp,
            'updated_at': timestamp,
            'message_count': 0
        }
        
        # Add to threads index
        threads = self.load_threads_index()
        threads.insert(0, thread_data)  # Add at the beginning (most recent)
        self.save_threads_index(threads)
        
        # Create empty chat history file
        self.save_thread_messages(thread_id, [])
        
        return thread_id
    
    def save_thread_messages(self, thread_id: str, messages: List[Dict]):
        """Save messages for a specific thread"""
        thread_file = self.chat_threads_dir / f"{thread_id}.json"
        
        with open(thread_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, default=str, ensure_ascii=False)
        
        # Update message count and timestamp in index
        self.update_thread_metadata(thread_id, {
            'message_count': len(messages),
            'updated_at': datetime.now().isoformat()
        })
    
    def load_thread_messages(self, thread_id: str) -> List[Dict]:
        """Load messages for a specific thread"""
        thread_file = self.chat_threads_dir / f"{thread_id}.json"
        
        if thread_file.exists():
            try:
                with open(thread_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def update_thread_metadata(self, thread_id: str, updates: Dict) -> bool:
        """Update thread metadata in the index - FIXED to return success status"""
        try:
            threads = self.load_threads_index()
            
            thread_found = False
            for thread in threads:
                if thread['thread_id'] == thread_id:
                    thread.update(updates)
                    thread_found = True
                    break
            
            if thread_found:
                self.save_threads_index(threads)
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Error updating thread metadata: {str(e)}")
            return False
    
    def update_thread_title(self, thread_id: str, new_title: str) -> bool:
        """Update thread title - FIXED to return success status"""
        try:
            success = self.update_thread_metadata(thread_id, {
                'title': new_title.strip(),
                'updated_at': datetime.now().isoformat()
            })
            return success
        except Exception as e:
            st.error(f"Error updating thread title: {str(e)}")
            return False
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a chat thread - ENHANCED error handling"""
        try:
            # Remove from index
            threads = self.load_threads_index()
            original_count = len(threads)
            threads = [t for t in threads if t['thread_id'] != thread_id]
            
            # Check if thread was actually found and removed
            if len(threads) == original_count:
                # Thread wasn't found in index
                st.warning(f"Thread {thread_id} not found in index")
                return False
            
            self.save_threads_index(threads)
            
            # Delete thread file
            thread_file = self.chat_threads_dir / f"{thread_id}.json"
            if thread_file.exists():
                thread_file.unlink()
            
            return True
            
        except Exception as e:
            st.error(f"Error deleting thread: {str(e)}")
            return False
    
    def get_thread_by_id(self, thread_id: str) -> Optional[Dict]:
        """Get thread metadata by ID"""
        threads = self.load_threads_index()
        return next((t for t in threads if t['thread_id'] == thread_id), None)
    
    def get_threads_for_pdf(self, pdf_file_id: str) -> List[Dict]:
        """Get all threads for a specific PDF"""
        threads = self.load_threads_index()
        return [t for t in threads if t.get('pdf_file_id') == pdf_file_id]
    
    def add_message_to_thread(self, thread_id: str, question: str, answer: str, sources: Optional[List[Dict]] = None):
        """Add a new message pair to a thread"""
        messages = self.load_thread_messages(thread_id)
        
        message_pair = {
            'question': question,
            'answer': answer,
            'sources': sources or [],
            'timestamp': datetime.now().isoformat()
        }
        
        messages.append(message_pair)
        self.save_thread_messages(thread_id, messages)
    
    def search_threads(self, query: str) -> List[Dict]:
        """Search threads by title or content"""
        threads = self.load_threads_index()
        query = query.lower()
        
        matching_threads = []
        for thread in threads:
            # Search in title
            if query in thread.get('title', '').lower():
                matching_threads.append(thread)
                continue
            
            # Search in messages
            messages = self.load_thread_messages(thread['thread_id'])
            for msg in messages:
                if (query in msg.get('question', '').lower() or 
                    query in msg.get('answer', '').lower()):
                    matching_threads.append(thread)
                    break
        
        return matching_threads
    
    def cleanup_orphaned_threads(self, valid_pdf_ids: List[str]) -> int:
        """Remove threads for PDFs that no longer exist - FIXED return count"""
        try:
            threads = self.load_threads_index()
            valid_threads = []
            deleted_count = 0
            
            for thread in threads:
                if thread.get('pdf_file_id') in valid_pdf_ids:
                    valid_threads.append(thread)
                else:
                    # Delete orphaned thread file
                    thread_file = self.chat_threads_dir / f"{thread['thread_id']}.json"
                    if thread_file.exists():
                        thread_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                self.save_threads_index(valid_threads)
            
            return deleted_count
            
        except Exception as e:
            st.error(f"Error cleaning up orphaned threads: {str(e)}")
            return 0
    
    def get_thread_stats(self) -> Dict:
        """Get statistics about stored threads"""
        try:
            threads = self.load_threads_index()
            
            if not threads:
                return {
                    'total_threads': 0,
                    'total_messages': 0,
                    'oldest_thread': None,
                    'newest_thread': None
                }
            
            total_messages = sum(t.get('message_count', 0) for t in threads)
            
            # Safe datetime handling
            def get_datetime(thread, field):
                dt = thread.get(field)
                if isinstance(dt, str):
                    try:
                        return datetime.fromisoformat(dt.replace('T', ' '))
                    except:
                        return datetime.min
                elif isinstance(dt, datetime):
                    return dt
                else:
                    return datetime.min
            
            oldest_thread = min(threads, key=lambda x: get_datetime(x, 'created_at'))
            newest_thread = max(threads, key=lambda x: get_datetime(x, 'created_at'))
            
            return {
                'total_threads': len(threads),
                'total_messages': total_messages,
                'oldest_thread': oldest_thread.get('created_at'),
                'newest_thread': newest_thread.get('created_at')
            }
            
        except Exception as e:
            st.error(f"Error getting thread stats: {str(e)}")
            return {
                'total_threads': 0,
                'total_messages': 0,
                'oldest_thread': None,
                'newest_thread': None
            }
    
    @staticmethod
    def format_datetime(dt) -> str:
        """Format datetime for display - ENHANCED error handling"""
        try:
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace('T', ' '))
                except:
                    return dt
            elif not isinstance(dt, datetime):
                return "Unknown"
            
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 3600:  # Less than 1 hour
                    minutes = diff.seconds // 60
                    return f"{minutes}m ago" if minutes > 0 else "Just now"
                else:  # Less than 1 day
                    hours = diff.seconds // 3600
                    return f"{hours}h ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days}d ago"
            else:
                return dt.strftime("%b %d")
                
        except Exception:
            return "Unknown"