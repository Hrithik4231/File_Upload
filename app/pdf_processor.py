import streamlit as st
from pathlib import Path
import fitz  
from typing import List, Dict, Tuple, Optional
from app.file_manager import FileManager
from app.chat_sidebar import ChatSidebar
from app.chat_memory import ChatMemoryManager


class PDFProcessor:
    """Class for PDF processing and text extraction"""
    def __init__(self):
        self.file_manager = FileManager()
        self.chat_memory = ChatMemoryManager()
        self.chat_sidebar = ChatSidebar(self.file_manager,self.chat_memory)
        # self.chat_ui = ChatWithPDFUI(self.file_manager, self.chat_sidebar)
        # self.pdf_processor = PDFProcessor()
    @staticmethod
    def extract_text_with_pages(pdf_path: Path) -> List[Dict]:
        """Extract text from PDF with page information"""
        try:
            doc = fitz.open(pdf_path)
            pages_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                pages_content.append({
                    'page_number': page_num + 1,
                    'content': text.strip()
                })
            
            doc.close()
            return pages_content
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return []
    
    @staticmethod
    def create_pdf_chunks(pages_content: List[Dict], chunk_size: int = 1000) -> List[Dict]:
        """Create chunks from PDF content for better processing"""
        chunks = []
        chunk_id = 0
        
        for page in pages_content:
            content = page['content']
            page_num = page['page_number']
            
            if len(content) <= chunk_size:
                chunks.append({
                    'chunk_id': chunk_id,
                    'page_number': page_num,
                    'content': content
                })
                chunk_id += 1
            else:
                # Split large pages into smaller chunks
                words = content.split()
                current_chunk = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) > chunk_size and current_chunk:
                        chunks.append({
                            'chunk_id': chunk_id,
                            'page_number': page_num,
                            'content': ' '.join(current_chunk)
                        })
                        chunk_id += 1
                        current_chunk = [word]
                        current_length = len(word)
                    else:
                        current_chunk.append(word)
                        current_length += len(word) + 1
                
                if current_chunk:
                    chunks.append({
                        'chunk_id': chunk_id,
                        'page_number': page_num,
                        'content': ' '.join(current_chunk)
                    })
                    chunk_id += 1
        
        return chunks