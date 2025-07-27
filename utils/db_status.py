"""Database status utilities"""
import streamlit as st
from database.robust_connection import db_manager

def display_db_status():
    """Display database connection status in the sidebar"""
    status = db_manager.get_status()
    
    if status['connected']:
        st.sidebar.success("✅ Database Connected")
        st.sidebar.caption(f"Type: {status['type']}")
    else:
        st.sidebar.warning("⚠️ Using Fallback Storage")
        st.sidebar.caption("Data won't persist between sessions")
    
    # Show recent connection messages if any
    if hasattr(st.session_state, 'db_messages') and st.session_state.db_messages:
        with st.sidebar.expander("Database Messages", expanded=False):
            for msg in st.session_state.db_messages[-3:]:  # Show last 3 messages
                st.caption(msg)

def check_db_connection():
    """Check and return database connection status"""
    return db_manager.get_status()['connected']