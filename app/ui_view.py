import streamlit as st
import base64
import pandas as pd
from typing import Dict
from app.file_manager import FileManager

class ViewUploadsUI:
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    def run(self):
        st.header("📁 View Uploaded Documents")

        metadata = self.file_manager.load_metadata()

        if not metadata:
            st.info("No documents uploaded yet. Go to 'Upload Document' to add files.")
            return

        # Reset selected preview file_id if not already set
        if 'selected_preview_file_id' not in st.session_state:
            st.session_state.selected_preview_file_id = None

        self.display_documents_table(metadata)

    def display_documents_table(self, metadata: Dict):
        # Sort files by creation date (newest first)
        sorted_files = sorted(
            metadata.items(), 
            key=lambda x: x[1].get('created_at', ''), 
            reverse=True
        )

        # Prepare data for the table
        table_data = []
        for index, (file_id, file_info) in enumerate(sorted_files, 1):
            # Get status with emoji
            status = file_info.get('status', 'unknown')
            status_display = self.get_status_display(status)
            
            table_data.append({
                'S.No': index,
                'Document Name': f"📄 {file_info.get('filename', 'Unknown')}",
                'Size': self.file_manager.format_file_size(file_info.get('filesize', 0)),
                'Created At': self.file_manager.format_datetime(file_info.get('created_at', '')),
                'Status': status_display
            })

        # Create DataFrame
        df = pd.DataFrame(table_data)
        
        # Display the table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'S.No': st.column_config.NumberColumn(
                    "S.No",
                    width="small",
                ),
                'Document Name': st.column_config.TextColumn(
                    "Document Name",
                    width="large",
                ),
                'Size': st.column_config.TextColumn(
                    "Size",
                    width="small",
                ),
                'Created At': st.column_config.TextColumn(
                    "Created At",
                    width="medium",
                ),
                'Status': st.column_config.TextColumn(
                    "Status",
                    width="small",
                )
            }
        )

        # Display action buttons for each file
        st.markdown("### Actions")
        for index, (file_id, file_info) in enumerate(sorted_files, 1):
            self.create_action_buttons(index, file_id, file_info)
            
            # Show preview if this file is selected
            if st.session_state.selected_preview_file_id == file_id:
                self.render_pdf_preview(file_id, file_info)

    def create_action_buttons(self, serial_number: int, file_id: str, file_info: Dict):
        # Create columns for buttons - aligned with the table structure
        col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 3, 1, 1.5, 1, 1, 1])
        
        with col1:
            st.write(f"{serial_number}.")
        
        with col2:
            st.write(f"📄 {file_info.get('filename', 'Unknown')}")
        
        with col6:
            # Preview button
            preview_key = f"preview_{file_id}"
            if st.button("👁️ Preview", key=preview_key):
                if st.session_state.selected_preview_file_id == file_id:
                    # If already previewing this file, hide preview
                    st.session_state.selected_preview_file_id = None
                else:
                    # Show preview for this file
                    st.session_state.selected_preview_file_id = file_id
                st.rerun()
        
        with col7:
            # Delete button
            delete_key = f"delete_{file_id}"
            if st.button("🗑️ Delete", key=delete_key):
                if self.file_manager.delete_file(file_id):
                    st.success(f"Deleted '{file_info['filename']}'")
                    st.session_state.selected_preview_file_id = None
                    st.rerun()
                else:
                    st.error("Failed to delete file")

    def get_status_display(self, status: str) -> str:
        """Generate status display with appropriate emoji."""
        status_configs = {
            'success': '🟢 Success',
            'error': '🔴 Failed',
            'processing': '🟠 Processing',
            'uploading': '🟡 Uploading'
        }
        
        return status_configs.get(status.lower(), f'⚪ {status.title()}')

    def render_pdf_preview(self, file_id: str, file_info: Dict):
        """Render PDF preview below the selected row."""
        st.markdown("---")
        
        # Preview header with close button
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(f"### 📄 Preview: {file_info['filename']}")
        with col2:
            if st.button("✖️ Close", key=f"close_preview_{file_id}"):
                st.session_state.selected_preview_file_id = None
                st.rerun()

        file_path = self.file_manager.get_file_path(file_id)

        if file_path and file_path.exists():
            try:
                with open(file_path, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode("utf-8")

                # PDF viewer
                pdf_display = f"""
                <div style="display: flex; justify-content: center; margin: 20px 0;">
                    <iframe 
                        src="data:application/pdf;base64,{base64_pdf}" 
                        width="100%" 
                        height="600" 
                        type="application/pdf" 
                        style="border: 2px solid #555; border-radius: 8px;">
                        <p>Your browser does not support PDFs. 
                        <a href="data:application/pdf;base64,{base64_pdf}">Download the PDF</a>.</p>
                    </iframe>
                </div>
                """

                st.markdown(pdf_display, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error previewing PDF: {str(e)}")
        else:
            st.error("File not found")

        st.markdown("---")