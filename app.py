"""
Opportunity Inbox Copilot — Gmail-Themed Streamlit App
SOFTEC 2026 AI Hackathon
"""

import streamlit as st
import sys
import os
import base64
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from models.schemas import StudentProfile
from controller.pipeline import run_pipeline
from database.db import (
    init_db, init_emails_table, add_email, get_all_emails, get_emails_by_status,
    update_email_status, reset_all_email_statuses, delete_all_emails,
    get_email_counts, has_any_emails, save_config, get_config,
    get_opportunity_by_email_text
)
from utils.helpers import split_emails, days_until, urgency_label
from utils.sample_emails import SAMPLE_EMAILS_TEXT
from utils.summarizer import get_ai_summary

# ──────────────────────────────────────────
# Page config
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Opportunity Inbox Copilot",
    page_icon="📨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# Integrated Gmail Material You CSS
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500&display=swap');

/* Updated Gmail Material You Palette */
:root {
    --primary-white: #FFFFFF;
    --google-blue: #0B57D0;
    --sidebar-bg: #F3E8FF; /* Light purplish background for sidebar */
    --search-bar-bg: #F1F3F4;
    --hover-state: #F3E8FF;
    --border-divider: #E0E2E6;
    --text-primary: #1F1F1F;
    --text-secondary: #444746;
    --sidebar-accent: #D3E3FD; /* The blueish highlight for active items */
    --soft-purple: #F3E8FF;
    --deep-purple: #6B21A8;
}

/* Global styles */
.stApp {
    font-family: 'Google Sans', 'Roboto', sans-serif;
    background-color: #FDFBFF; /* Slightly purplish main background */
}

/* Fix for Sidebar "Black Divs" and Input Containers */
[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg);
    border-right: 1px solid var(--border-divider);
}

/* This targets the input wrapper boxes to make them clean and white */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
    background-color: transparent !important;
    border: none !important;
    padding: 0px !important;
}

/* Style the actual input widgets in the sidebar */
[data-testid="stSidebar"] .stTextInput input, 
[data-testid="stSidebar"] .stNumberInput input, 
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
    background-color: var(--sidebar-bg) !important;
    border: 1px solid var(--border-divider) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* Ensure sidebar labels are black for contrast on purplish background */
[data-testid="stSidebar"] label, 
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stSelectbox span {
    color: #000000 !important;
}

/* Custom Purple Labeling for Sidebar Header */
.sidebar-header {
    padding: 20px 0px;
    font-family: 'Google Sans';
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--deep-purple);
    border-bottom: 1px solid var(--soft-purple);
    margin-bottom: 20px;
}

/* Sidebar Form Container Styling */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
}

/* Professional Top Bar */
.top-bar {
    display: flex;
    align-items: center;
    padding: 8px 16px;
    background-color: var(--primary-white);
    border-bottom: 1px solid var(--border-divider);
}

/* Compose-style Button (Primary Action) */
div.stButton > button[kind="primary"] {
    background-color: var(--sidebar-accent) !important;
    color: #041E49 !important;
    border: none !important;
    padding: 12px 24px !important;
    border-radius: 16px !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15) !important;
    width: 100% !important; /* Force width for the header button */
}

div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 1px 3px 0 rgba(60,64,67,.3), 0 4px 8px 3px rgba(60,64,67,.15) !important;
}

/* Secondary Buttons */
div.stButton > button:not([kind="primary"]) {
    border-radius: 20px !important;
    background-color: var(--primary-white) !important;
    border: 1px solid var(--border-divider) !important;
    color: var(--text-secondary) !important;
}

/* Row Styling: Inbox List */
.email-row-container {
    padding: 0;
}

.email-row-style {
    border-bottom: 1px solid #F1F3F4;
    padding: 4px 16px;
    display: flex;
    align-items: center;
    transition: all 0.2s;
}

.email-row-style.pending { background-color: #cbc3e3; }
.email-row-style.opportunity { background-color: #e6fffa; }
.email-row-style.spam { background-color: #fdf2f2; }

.email-row-style:hover {
    box-shadow: inset 1px 0 0 #dadce0, inset -1px 0 0 #dadce0, 0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15);
    z-index: 1;
    filter: brightness(0.97);
}

.status-label {
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    margin-right: 15px;
    text-transform: uppercase;
    min-width: 25px;
    text-align: center;
}

.status-label.pending { background-color: #f1f3f4; color: var(--text-secondary); }
.status-label.opportunity { background-color: #e6fffa; color: #00695c; }
.status-label.spam { background-color: #fdf2f2; color: #c62828; }

/* AI Recommendation Box (Purple Accent) */
.ai-recommendation-box {
    background: linear-gradient(135deg, #FAF5FF 0%, #F3E8FF 100%);
    border-left: 5px solid var(--deep-purple);
    border-radius: 8px;
    padding: 24px;
    margin: 20px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* Main Page Tabs Styling (Opportunities, Add, etc. in black) */
.stTabs [data-baseweb="tab"] {
    color: #000000 !important;
    font-weight: 500;
}

.stTabs [aria-selected="true"] {
    color: var(--deep-purple) !important;
    border-bottom-color: var(--deep-purple) !important;
}

/* Detail View Wrapper */
.detail-wrapper {
    color: #000000 !important;
    background-color: #FFFFFF !important;
    border-radius: 8px;
    padding: 24px;
    border: 1px solid var(--border-divider);
}

.detail-wrapper h1, .detail-wrapper h2, .detail-wrapper h3, .detail-wrapper h4, .detail-wrapper p, .detail-wrapper span, .detail-wrapper div {
    color: #000000 !important;
}

/* Hide Default View */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# Database & Init
# ──────────────────────────────────────────
init_db()
init_emails_table()

if not has_any_emails():
    emails = split_emails(SAMPLE_EMAILS_TEXT)
    for e in emails:
        add_email(e)

if "selected_email_id" not in st.session_state:
    st.session_state.selected_email_id = None

saved_config = get_config()
if not saved_config:
    saved_config = {
        "degree": "BS", "program": "Computer Science", "semester": 5, "cgpa": 3.4,
        "skills": "Python, Machine Learning", "interests": "AI, Research",
        "preferred_types": ["Internship", "Scholarship"],
        "financial_need": True, "location_preference": "Any",
        "past_experience": "GSoC candidate."
    }
    save_config(saved_config)

# ──────────────────────────────────────────
# Sidebar: Setup
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ Profile Configuration</div>', unsafe_allow_html=True)
    
    with st.form("sidebar_config"):
        deg = st.selectbox("Current Degree", ["BS", "BE", "BBA", "MS", "PhD"], index=["BS", "BE", "BBA", "MS", "PhD"].index(saved_config["degree"]))
        pro = st.text_input("Major / Program", value=saved_config["program"])
        sem = st.number_input("Current Semester", 1, 12, value=saved_config["semester"])
        gpa = st.number_input("Current CGPA", 0.0, 4.0, value=saved_config["cgpa"], step=0.1)
        skl = st.text_input("Technical Skills", value=saved_config["skills"])
        its = st.text_input("Domain Interests", value=saved_config["interests"])
        opt = st.multiselect("Preferred Opps", ["Scholarship", "Internship", "Competition", "Fellowship", "Research"], default=saved_config["preferred_types"])
        nfd = st.checkbox("Financial Aid Search", value=saved_config["financial_need"])
        lcp = st.selectbox("Locality", ["Any", "Pakistan", "Remote", "International"], index=["Any", "Pakistan", "Remote", "International"].index(saved_config["location_preference"]))
        exp = st.text_area("Experience Brief", value=saved_config["past_experience"], height=100)
        
        if st.form_submit_button("Save & Refresh Inbox"):
            new_c = {
                "degree": deg, "program": pro, "semester": sem, "cgpa": gpa,
                "skills": skl, "interests": its, "preferred_types": opt,
                "financial_need": nfd, "location_preference": lcp, "past_experience": exp
            }
            save_config(new_c)
            reset_all_email_statuses()
            st.toast("Profile updated. ✓", icon="✅")
            st.rerun()
            
    st.markdown("---")
    if st.button("🗑️ Clear All Emails"):
        delete_all_emails()
        st.rerun()

# ──────────────────────────────────────────
# Main App Header
# ──────────────────────────────────────────
st.markdown('<div class="top-bar">', unsafe_allow_html=True)
col_h_left, col_h_mid, col_h_right = st.columns([1.5, 3, 1.2])

with col_h_left:
    logo_b64 = ""
    try:
        with open("logo.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
    except Exception:
        pass
    
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height: 28px; margin-right: 12px; vertical-align: middle;">' if logo_b64 else '📨 '
    st.markdown(f'<div style="font-size: 1.4rem; font-weight: 500; color: var(--text-secondary); display: flex; align-items: center;">{img_tag}Opportunity Inbox Copilot</div>', unsafe_allow_html=True)

with col_h_mid:
    st.text_input("Search", placeholder="Search opportunities...", label_visibility="collapsed", key="search_bar")

with col_h_right:
    pending_emails = get_emails_by_status("pending")
    # type="primary" renders as kind="primary" in current Streamlit
    if st.button("Find Opportunities", key="main_run_btn", type="primary"):
        if not pending_emails:
            st.toast("No pending mail. ✓")
        else:
            with st.spinner("Analyzing..."):
                texts = [e['raw_text'] for e in pending_emails]
                profile = StudentProfile(
                    degree=saved_config["degree"], program=saved_config["program"],
                    semester=saved_config["semester"], cgpa=saved_config["cgpa"],
                    skills=[s.strip() for s in saved_config["skills"].split(",") if s.strip()],
                    interests=[s.strip() for s in saved_config["interests"].split(",") if s.strip()],
                    preferred_types=[t.lower() for t in saved_config["preferred_types"]],
                    financial_need=saved_config["financial_need"],
                    location_preference=saved_config["location_preference"],
                    past_experience=saved_config["past_experience"]
                )
                ranked, discarded = run_pipeline(texts, profile)
                
                id_map = {e['raw_text']: e['id'] for e in pending_emails}
                for r in ranked:
                    update_email_status(id_map[r.raw_email], "opportunity")
                for d in discarded:
                    txt = texts[d['email_index']]
                    update_email_status(id_map[txt], "spam", d['reason'])
                    
                st.toast("Sorting complete. ✓", icon="✅")
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ─── Navigation ───
counts = get_email_counts()
tab1, tab2, tab3, tab4 = st.tabs([
    f"Inbox ({counts['pending'] + counts['opportunity'] + counts['spam']})",
    f"Opportunities ({counts['opportunity']})",
    f"Spam ({counts['spam']})",
    "➕ Add"
])

def render_list(status=None, prefix="all"):
    emails = get_emails_by_status(status) if status else get_all_emails()
    
    search_query = st.session_state.get("search_bar", "").strip().lower()
    if search_query:
        emails = [e for e in emails if search_query in (e['subject_snippet'] or "").lower() 
                  or search_query in (e['sender_snippet'] or "").lower() 
                  or search_query in (e['raw_text'] or "").lower()]

    if not emails:
        st.markdown("<div style='padding: 80px; text-align: center; color: var(--text-secondary);'>Clean inbox. ✓</div>", unsafe_allow_html=True)
        return

    for em in emails:
        sender = em['sender_snippet'] or "System"
        subj = em['subject_snippet'] or "(No Subject)"
        body = em['raw_text'][:120].replace('\n', ' ')
        
        with st.container():
            st.markdown(f'<div class="email-row-style {em["status"]}">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([0.1, 4, 0.4])
            with c1:
                st.markdown(f"<div class='status-label {em['status']}'>{em['status'][0].upper()}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div><span style='font-weight:500; color:var(--text-primary); width:150px; display:inline-block;'>{sender[:18]}</span> <span style='font-weight:500; color:var(--text-primary);'>{subj}</span> <span style='color:var(--text-secondary);'> - {body}...</span></div>", unsafe_allow_html=True)
            with c3:
                if st.button("Open", key=f"btn_{prefix}_{em['id']}"):
                    st.session_state.selected_email_id = em['id']
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# Detail View
if st.session_state.selected_email_id:
    # Overlay context
    selected = next((x for x in get_all_emails() if x['id'] == st.session_state.selected_email_id), None)
    if selected:
        st.markdown('''<style>
            [data-testid="stMarkdownContainer"] p, 
            [data-testid="stMarkdownContainer"] h1, 
            [data-testid="stMarkdownContainer"] h2, 
            [data-testid="stMarkdownContainer"] h3, 
            [data-testid="stMarkdownContainer"] h4, 
            [data-testid="stMarkdownContainer"] span, 
            [data-testid="stMarkdownContainer"] li,
            [data-testid="stMetricValue"], 
            [data-testid="stMetricLabel"] {
                color: #000000 !important;
            }
        </style>''', unsafe_allow_html=True)
        if st.button("← Back to List"):
            st.session_state.selected_email_id = None
            st.rerun()
            
        st.markdown(f"## {selected['subject_snippet'] or '(No Subject)'}")
        st.markdown(f"**From:** {selected['sender_snippet'] or 'Unknown'}")
        
        if selected['status'] == 'opportunity':
            opp = get_opportunity_by_email_text(selected['raw_text'])
            if opp:
                st.markdown("---")

                # AI Insight Summary at the top
                st.markdown('<div class="ai-recommendation-box">', unsafe_allow_html=True)
                st.markdown("### ✨ AI Insight Summary")
                st.markdown(get_ai_summary(opp))
                st.markdown('</div>', unsafe_allow_html=True)

                # Title and Basic Info
                st.markdown(f"### 🏆 Application Details: {opp.get('title', 'Unknown Title')} ({opp.get('opp_type', 'opportunity').title()})")
                
                # Calculation Metrics
                st.markdown("#### 📊 Calculation Metrics")
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Final", f"{int(opp.get('final_score', 0) * 10)}%")
                m2.metric("Match", f"{int(opp.get('profile_match_score', 0) * 10)}%")
                m3.metric("Urgency", f"{int(opp.get('urgency_score', 0) * 10)}%")
                m4.metric("Pref.", f"{int(opp.get('preference_score', 0) * 10)}%")
                m5.metric("Complete", f"{int(opp.get('completeness_score', 0) * 10)}%")
                m6.metric("Value", f"{int(opp.get('value_score', 0) * 10)}%")

                # Extracted Properties
                st.markdown("#### 📝 Key Details")
                st.markdown(f"**Organization:** {opp.get('organization', 'N/A')}  |  **Location:** {opp.get('location', 'N/A')}  |  **Stipend:** {opp.get('stipend_or_amount', 'N/A')}")
                st.markdown(f"**Deadline:** {opp.get('deadline_raw', 'N/A')}  |  **Contact:** {opp.get('contact', 'N/A')}")
                if opp.get('link'):
                    st.markdown(f"**Link:** [{opp['link']}]({opp['link']})")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Eligibility:**")
                    elig = opp.get('eligibility_json', [])
                    if elig:
                        for e in elig: st.markdown(f"✓ {e}")
                    else: st.markdown("Not specified")
                with col_b:
                    st.markdown("**Required Documents:**")
                    docs = opp.get('required_documents_json', [])
                    if docs:
                        for d in docs: st.markdown(f"✓ {d}")
                    else: st.markdown("Not specified")
                
                st.markdown("---")
                
                col_c, col_d = st.columns(2)
                with col_c:
                    st.markdown("#### ✅ Action Checklist")
                    for cl in opp.get('checklist_json', []):
                        st.markdown(f"✓ {cl}")
                with col_d:
                    st.markdown("#### 🧠 Strategic Logic")
                    st.info(opp.get('why', 'No explanation provided.'))
        elif selected['status'] == 'spam':
            st.error(f"Classified as Spam: {selected['spam_reason']}")
            
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

with tab1: render_list(prefix="inbox")
with tab2: render_list("opportunity", prefix="opp")
with tab3: render_list("spam", prefix="spam")
with tab4:
    st.markdown('<style>[data-testid="stFileUploader"] label, [data-testid="stTextArea"] label p { color: #000000 !important; }</style>', unsafe_allow_html=True)
    st.markdown("<h1 style='color: #000000; margin-top: 0;'>Import Emails</h1>", unsafe_allow_html=True)
    paste = st.text_area("Paste Content (--- separator)", height=200)
    if st.button("Import Emails", type="primary", key="import_btn"):
        if paste:
            ems = split_emails(paste)
            for e in ems: add_email(e)
            st.toast("Success! ✓")
            st.rerun()
    st.markdown("---")
    file = st.file_uploader("Upload .txt")
    if file:
        content = file.getvalue().decode("utf-8")
        ems = split_emails(content)
        for e in ems: add_email(e)
        st.toast("Loaded. ✓")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br><hr><div style='text-align: center; color: var(--text-secondary); padding: 20px;'>Opportunity Inbox Copilot ✓ AI Solution</div>", unsafe_allow_html=True)
