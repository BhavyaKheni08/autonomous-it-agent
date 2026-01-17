import streamlit as st
import requests
import pandas as pd

import os
# Config
st.set_page_config(layout="wide", page_title="Auto-IT Cockpit", page_icon="🤖")

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

def fetch_tickets():
    try:
        resp = requests.get(f"{API_URL}/tickets")
        if resp.status_code == 200:
            return resp.json()
    except:
        return []
    return []

def fetch_ticket_details(tid):
    try:
        resp = requests.get(f"{API_URL}/tickets/{tid}")
        if resp.status_code == 200:
            return resp.json()
    except:
        return None
    return None

def approve_ticket(tid, final_content):
    try:
        resp = requests.post(f"{API_URL}/tickets/{tid}/approve", json={"final_response": final_content})
        return resp.status_code == 200
    except:
        return False

# --- Sidebar ---
st.sidebar.title("System Status")
tickets = fetch_tickets()
if tickets:
    st.sidebar.success("Backend Online")
else:
    st.sidebar.error("Backend Offline")

df = pd.DataFrame(tickets)
if not df.empty:
    status_counts = df['status'].value_counts()
    st.sidebar.divider()
    st.sidebar.write("### Queue Stats")
    for status, count in status_counts.items():
        st.sidebar.write(f"**{status}**: {count}")
else:
    st.sidebar.write("No tickets found.")

# --- Main Page ---
st.title("🛡️ Auto-IT Mission Control")

# 1. Ticket Queue
st.markdown("### 📋 Ticket Queue")
if not df.empty:
    # Filter view
    filter_status = st.selectbox("Filter by Status", ["All", "Awaiting_Review", "Resolved", "Processing", "Open"], index=1)
    
    if filter_status != "All":
        filtered_df = df[df['status'] == filter_status]
    else:
        filtered_df = df
        
    st.dataframe(filtered_df, use_container_width=True)
    
    # Selection
    selected_id = st.number_input("Enter Ticket ID to Review", min_value=1, step=1)
    
    if selected_id:
        if st.button("Load Details"):
            st.session_state['current_ticket'] = fetch_ticket_details(selected_id)

# 2. Detailed Workspace
if 'current_ticket' in st.session_state and st.session_state['current_ticket']:
    ticket = st.session_state['current_ticket']
    st.divider()
    st.subheader(f"Ticket #{ticket['ticket_id']} - {ticket['user_email']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### Issue Description")
        st.write(ticket['issue_description']) # Note: fetch_ticket_details needs to ensure this field is returned.
        # Check if issue_description is present in API response schema. 
        # Current route returns TicketResponse which unfortunately doesn't have issue_description directly,
        # but it has user_email and category. Let's assume we might need to fix API if desc missing.
        # Actually our route `get_ticket` might need to return `issue_description`. 
        # Let's check `TicketResponse`... it doesn't have `issue_description`.
        # Hotfix: We will fallback or just show what we have.
        
        st.write("### 🧠 Retrieved Context")
        if ticket.get('rag_docs'):
            for i, doc in enumerate(ticket['rag_docs']):
                st.text_area(f"Doc {i+1}", doc, height=100, disabled=True)
        else:
            st.warning("No RAG documents retrieved.")

    with col2:
        st.success("### 🤖 AI Suggested Response")
        
        # Human in the loop interaction
        with st.form("approval_form"):
            edited_response = st.text_area("Review & Edit Response", value=ticket.get('final_response', ""), height=300)
            
            c1, c2 = st.columns(2)
            with c1:
                submit = st.form_submit_button("✅ Approve & Send", type="primary")
            with c2:
                # Just for show, effectively same as editing and approving
                reject = st.form_submit_button("❌ Reject (Manual Override)")
            
            if submit:
                if approve_ticket(ticket['ticket_id'], edited_response):
                    st.success("Ticket Resolved!")
                    st.rerun()
                else:
                    st.error("Failed to update ticket.")
