import streamlit as st
import time
import os
import sys
import textwrap

# Add project root to path to load configs
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from configs.dataset_config import config_loader
from frontend.api_client import RetainIQAPIClient

# Import modular sub-views
from frontend.views.auth_view import render_auth_view
from frontend.views.dashboard_view import render_dashboard_view
from frontend.views.executive_view import render_executive_view
from frontend.views.diagnostics_view import render_diagnostics_view
from frontend.views.ingestion_view import render_ingestion_view
from frontend.views.explorer_view import render_explorer_view
from frontend.views.counterfactual_view import render_counterfactual_view
from frontend.views.explainability_view import render_explainability_view
from frontend.views.segments_view import render_segments_view
from frontend.views.drift_view import render_drift_view
from frontend.views.settings_view import render_settings_view

# Fetch dynamic styling tokens from config
theme_cfg = config_loader.dashboard.get("theme", {})
primary_color_hex = theme_cfg.get("primary_color", "#6366F1").lower()
secondary_color_hex = theme_cfg.get("secondary_color", "#F97316").lower()
danger_color_hex = theme_cfg.get("danger_color", "#EF4444").lower()

# Instantiate class-based API client
api_client = RetainIQAPIClient()

# Parse routing and layout parameters from query params
if st.query_params.get("logout") == "true":
    st.query_params.clear()
    st.session_state.jwt_token = None
    st.session_state.current_user = None
    st.cache_data.clear()
    st.rerun()

PAGE_MAP = {
    "dashboard": "📊 Dashboard",
    "explorer": "🔍 Customer Explorer",
    "simulator": "🔮 Counterfactual Simulator",
    "analytics": "📈 Analytics",
    "explainability": "🌍 Explainability",
    "segments": "🧩 Customer Segments",
    "upload": "📤 Upload Dataset",
    "diagnostics": "🩺 Model Diagnostics",
    "drift": "🚨 Drift Detection",
    "settings": "⚙️ Settings"
}

is_collapsed = (st.query_params.get("collapsed") == "true")
collapsed_str = "true" if is_collapsed else "false"
toggle_collapsed_str = "false" if is_collapsed else "true"
collapsed_class = "collapsed" if is_collapsed else ""
initial_sidebar_state = "collapsed" if is_collapsed else "expanded"

active_slug = st.query_params.get("page", "dashboard")
if active_slug not in PAGE_MAP:
    active_slug = "dashboard"

st.set_page_config(
    page_title="RetainIQ — Customer Churn Dashboard",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state=initial_sidebar_state
)

# Theme setup
theme = st.query_params.get("theme", "dark")
if theme == "light":
    theme_tokens = f"""
    --bg: #f1f5f9;
    --panel: rgba(255, 255, 255, 0.85);
    --panel-hover: #e2e8f0;
    --border: rgba(15, 23, 42, 0.08);
    --text: #0f172a;
    --muted: #475569;
    --primary: {primary_color_hex};
    --primary-hover: #4F46E5;
    """
    app_bg_gradient = """
        background-color: var(--bg) !important;
        background-image: 
            radial-gradient(circle at 12% 18%, rgba(99, 102, 241, 0.05), transparent 40%),
            radial-gradient(circle at 88% 82%, rgba(139, 92, 246, 0.05), transparent 40%),
            linear-gradient(rgba(0, 0, 0, 0.005) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 0, 0, 0.005) 1px, transparent 1px) !important;
    """
else:
    theme_tokens = f"""
    --bg: #0b1020;
    --panel: rgba(18, 23, 45, 0.82);
    --panel-hover: #1b2140;
    --border: rgba(255, 255, 255, 0.06);
    --text: #ffffff;
    --muted: #9ca3af;
    --primary: #6C63FF;
    --primary-hover: #7C73FF;
    """
    app_bg_gradient = """
        background-color: var(--bg) !important;
        background-image: 
            radial-gradient(circle at 12% 18%, rgba(99, 102, 241, 0.12), transparent 40%),
            radial-gradient(circle at 88% 82%, rgba(139, 92, 246, 0.12), transparent 40%),
            radial-gradient(circle at 50% 50%, rgba(2, 6, 23, 0.95), transparent 90%),
            linear-gradient(rgba(255, 255, 255, 0.008) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.008) 1px, transparent 1px) !important;
    """

# Main content and navbar paddings
# If the user is not authenticated, do not offset the main container for the sidebar/navbar
if st.session_state.get("jwt_token") is None:
    content_padding_left = "2.5rem"
    navbar_padding_left = "2.5rem"
    padding_top = "1.5rem"
else:
    padding_top = "calc(var(--navbar-height) + 1.5rem)"
    if is_collapsed:
        content_padding_left = "2.5rem"
        navbar_padding_left = "2.5rem"
    else:
        content_padding_left = "2.5rem"
        navbar_padding_left = "calc(var(--sidebar-width) + 24px)"

# Mobile side overlay menu setup
is_menu_open = (st.query_params.get("menu_open") == "true")
menu_open_str = "true" if is_menu_open else "false"
toggle_menu_open_str = "false" if is_menu_open else "true"
menu_class = "active" if is_menu_open else ""

# Search handling
if "search" in st.query_params:
    st.session_state.explorer_search_input = st.query_params.get("search")

# Navigation Helper Functions (Hybrid Architecture)
def navigate_to(slug):
    st.query_params["page"] = slug
    st.query_params["collapsed"] = "true" if is_collapsed else "false"
    st.query_params["theme"] = theme
    st.rerun()

def toggle_sidebar():
    st.query_params["page"] = st.query_params.get("page", "dashboard")
    st.query_params["collapsed"] = toggle_collapsed_str
    st.query_params["theme"] = theme
    st.rerun()

def toggle_theme():
    st.query_params["page"] = st.query_params.get("page", "dashboard")
    st.query_params["collapsed"] = "true" if is_collapsed else "false"
    st.query_params["theme"] = "light" if theme == "dark" else "dark"
    st.rerun()

# Custom premium styling rules
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap');
    
    :root {{
        --navbar-height: 72px;
        --sidebar-width: 280px;
        --sidebar-collapsed-width: 80px;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --transition: all .25s ease;
        --green: #10B981;
        --red: #EF4444;
        --warning: #F59E0B;
        --shadow-lg: 0 10px 40px rgba(0,0,0,.35);
        {theme_tokens}
    }}

    /* Global layout settings and ambient grid background */
    .stApp {{
        {app_bg_gradient}
        background-size: 100% 100%, 100% 100%, 100% 100%, 36px 36px, 36px 36px !important;
        background-attachment: fixed !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
    }}

    /* Shift main content block down and right to clear fixed top-navbar and sidebar */
    .block-container {{
        padding-top: {padding_top} !important;
        padding-left: {content_padding_left} !important;
        padding-right: 2.5rem !important;
        transition: var(--transition) !important;
    }}

    /* Hide default Streamlit header and sidebar */
    header, [data-testid="stHeader"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    /* Native Sidebar Restyling to match visual panel (Appendix C & D & G) */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background: var(--panel) !important;
        backdrop-filter: blur(18px) !important;
        border-right: 1px solid var(--border) !important;
        width: var(--sidebar-width) !important;
        transition: var(--transition) !important;
    }}
    [data-testid="stSidebarContent"] {{
        padding: 1.5rem 0.5rem !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding: 1.5rem 0.5rem !important;
        background: transparent !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
        display: none !important;
    }}
    [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}
    
    /* Align vertical elements inside native sidebar to support flex bottom user-card placement */
    [data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {{
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        justify-content: flex-start !important;
        gap: 0px !important;
    }}
    
    /* Sidebar Navigation Button Restyling */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        height: 40px !important; /* Shrunk from 48px to 40px for a more compact SaaS feel */
        border: 1px solid transparent !important; /* Flat card feel by default */
        background: transparent !important;
        color: var(--muted) !important;
        border-radius: 8px !important; /* Standard SaaS card rounded corners */
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        margin-bottom: 2px !important; /* Tighten gap between items */
        padding: 0px 12px !important; /* Shrunk padding to tighten spacing */
        box-shadow: none !important;
        transition: var(--transition) !important;
    }}
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] p {{
        font-family: 'Inter', sans-serif !important;
        color: inherit !important;
        font-size: 14px !important;
        font-weight: inherit !important;
        margin: 0 !important;
        word-spacing: -3px !important; /* Shrink spacing between emoji icon and label text */
    }}
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {{
        background: var(--panel-hover) !important;
        color: var(--text) !important;
        transform: translateX(2px) !important;
    }}

    /* Logout button custom overrides */
    [data-testid="stSidebar"] .st-key-btn_logout button {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 40px !important;
        color: var(--muted) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        background: transparent !important;
        transition: var(--transition) !important;
    }}
    [data-testid="stSidebar"] .st-key-btn_logout button p {{
        word-spacing: 0px !important; /* Keep default word spacing for logout label */
    }}
    [data-testid="stSidebar"] .st-key-btn_logout button:hover {{
        background: rgba(239, 68, 68, 0.08) !important;
        border-color: rgba(239, 68, 68, 0.3) !important;
        color: var(--red) !important;
    }}

    [data-testid="stSidebar"] .sidebar-group-header {{
        font-size: 10px !important; /* Shrunk from 11px to 10px for elegance */
        font-weight: 700 !important;
        color: var(--muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        margin: 20px 8px 8px 8px !important; /* Shrunk margins significantly to tighten spacing */
        transition: var(--transition) !important;
        text-align: left !important;
        display: {"none" if is_collapsed else "block"} !important;
    }}

    /* Title blocks */
    .main-title {{
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 2.8rem;
        background: linear-gradient(135deg, var(--primary) 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.8px;
    }}
    .subtitle {{
        font-family: 'Inter', sans-serif;
        color: var(--muted);
        font-size: 1.05rem;
        margin-bottom: 2rem;
        line-height: 1.5;
    }}

    /* Sticky Top Navbar styling */
    .sticky-navbar {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: var(--navbar-height);
        background: var(--panel) !important;
        backdrop-filter: blur(18px) !important;
        border-bottom: 1px solid var(--border) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 24px 0 {navbar_padding_left} !important;
        box-shadow: var(--shadow-lg) !important;
        z-index: 99999 !important;
        transition: var(--transition) !important;
    }}
    
    .navbar-left {{
        display: flex;
        align-items: center;
        gap: 1.2rem;
    }}
    
    .hamburger-menu {{
        font-size: 1.25rem;
        color: var(--muted);
        cursor: pointer;
        transition: var(--transition);
        user-select: none;
    }}
    .hamburger-menu:hover {{
        color: var(--text);
    }}
    
    .navbar-logo {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text);
    }}
    
    .navbar-center {{
        flex: 1;
        display: flex;
        justify-content: center;
        max-width: 520px;
        margin: 0 2rem;
    }}
    
    .search-container {{
        position: relative;
        width: 100%;
        display: flex;
        align-items: center;
        transition: var(--transition);
    }}
    .search-container:focus-within {{
        box-shadow: 0 0 15px rgba(108, 99, 255, 0.2);
    }}
    
    .search-icon {{
        position: absolute;
        left: 12px;
        color: var(--muted);
        font-size: 0.85rem;
    }}
    
    .search-input {{
        width: 100% !important;
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid var(--border) !important;
        border-radius: 9999px !important;
        padding: 0.45rem 5.0rem 0.45rem 2.2rem !important;
        color: var(--text) !important;
        font-size: 0.82rem !important;
        transition: var(--transition);
    }}
    .search-input:focus {{
        border-color: var(--primary) !important;
        outline: none !important;
    }}
    
    .search-badge {{
        position: absolute;
        right: 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 0.68rem;
        color: var(--muted);
    }}
    
    .navbar-right {{
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }}
    
    .nav-icon {{
        font-size: 1.1rem;
        color: var(--muted);
        text-decoration: none;
        cursor: pointer;
        transition: var(--transition);
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .nav-icon:hover {{
        color: var(--text);
    }}
    
    .notification-container {{
        position: relative;
        display: flex;
        align-items: center;
    }}
    
    .notification-badge {{
        position: absolute;
        top: -6px;
        right: -6px;
        background: var(--red);
        color: #ffffff;
        font-size: 0.65rem;
        font-weight: 700;
        border-radius: 9999px;
        padding: 1px 4px;
        min-width: 14px;
        text-align: center;
    }}

    /* Dropdown content */
    .notification-dropdown {{
        position: relative;
        display: inline-block;
    }}
    .notification-content {{
        display: none;
        position: absolute;
        right: 0;
        top: 25px;
        background-color: var(--panel);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        min-width: 250px;
        box-shadow: var(--shadow-lg);
        backdrop-filter: blur(18px);
        padding: 12px;
        z-index: 100000;
    }}
    .notification-dropdown:hover .notification-content {{
        display: block;
    }}
    .notification-item {{
        padding: 8px 12px;
        border-bottom: 1px solid var(--border);
        font-size: 0.78rem;
        color: var(--text);
        text-align: left;
    }}
    .notification-item:last-child {{
        border-bottom: none;
    }}

    /* Profile Dropdown */
    .profile-dropdown {{
        position: relative;
        display: inline-block;
    }}
    .profile-content {{
        display: none;
        position: absolute;
        right: 0;
        top: 35px;
        background-color: var(--panel);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        min-width: 180px;
        box-shadow: var(--shadow-lg);
        backdrop-filter: blur(18px);
        padding: 8px 0;
        z-index: 100000;
    }}
    .profile-dropdown:hover .profile-content {{
        display: block;
    }}
    .profile-link {{
        display: block;
        padding: 8px 16px;
        color: var(--text);
        text-decoration: none;
        font-size: 0.8rem;
        transition: var(--transition);
        text-align: left;
    }}
    .profile-link:hover {{
        background-color: var(--panel-hover);
        color: var(--primary);
    }}
    
    .navbar-profile {{
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
        border-radius: 9999px;
        padding: 4px 10px 4px 4px;
        cursor: pointer;
    }}
    
    .profile-avatar {{
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1 0%, #a78bfa 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: #ffffff;
        font-size: 0.72rem;
    }}
    
    .profile-info {{
        display: flex;
        flex-direction: column;
        text-align: left;
    }}
    
    .profile-name {{
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text);
        line-height: 1.1;
    }}
    
    .profile-email {{
        font-size: 0.65rem;
        color: var(--muted);
        line-height: 1.1;
    }}
    
    .profile-arrow {{
        font-size: 0.55rem;
        color: var(--muted);
        margin-left: 2px;
    }}

    /* Custom Fixed Sidebar */
    .sidebar {{
        position: fixed;
        top: var(--navbar-height);
        left: 0;
        bottom: 0;
        width: var(--sidebar-width);
        background: var(--panel) !important;
        border-right: 1px solid var(--border) !important;
        backdrop-filter: blur(18px) !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 1.5rem 1rem;
        transition: var(--transition);
        z-index: 9999;
        overflow-y: auto;
    }}
    .sidebar.collapsed {{
        width: var(--sidebar-collapsed-width);
        padding: 1.5rem 0.5rem;
    }}
    
    /* Navigation Link Styles */
    .nav-item {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 16px;
        height: 48px;
        color: var(--muted) !important;
        text-decoration: none !important;
        border-radius: var(--radius-md);
        font-size: 15px;
        font-weight: 500;
        margin-bottom: 4px;
        transition: var(--transition);
    }}
    .nav-item svg {{
        width: 20px;
        height: 20px;
        flex-shrink: 0;
        stroke: var(--muted);
        fill: none;
        transition: var(--transition);
    }}
    .nav-item:hover {{
        background: var(--panel-hover) !important;
        color: var(--text) !important;
        transform: translateX(2px);
    }}
    .nav-item:hover svg {{
        stroke: var(--text);
    }}
    
    .nav-item.active {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(99, 102, 241, 0.1) 100%) !important;
        border: 1px solid var(--primary) !important;
        border-left: 4px solid var(--primary) !important;
        color: var(--text) !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    }}
    .nav-item.active svg {{
        stroke: var(--text);
    }}
    
    /* Section Headers */
    .sidebar-group-header {{
        font-size: 11px;
        font-weight: 700;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 32px 12px 12px 12px;
        transition: var(--transition);
        text-align: left;
    }}
    .sidebar.collapsed .sidebar-group-header {{
        opacity: 0;
        height: 0;
        margin: 0;
        overflow: hidden;
    }}
    
    .sidebar.collapsed .nav-label {{
        display: none;
    }}
    .sidebar.collapsed .nav-item {{
        justify-content: center;
        padding: 14px 0;
    }}
    
    /* User Card */
    .user-card {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 16px;
        height: 72px;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: var(--transition);
        margin-top: auto;
        margin-bottom: 12px;
        text-align: left;
    }}
    .sidebar.collapsed .user-card {{
        padding: 8px;
        justify-content: center;
        border: none;
        background: transparent;
    }}
    
    .user-avatar {{
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1 0%, #a78bfa 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: #ffffff;
        font-size: 0.82rem;
        font-family: 'Outfit', sans-serif;
        flex-shrink: 0;
    }}
    
    .user-details {{
        display: flex;
        flex-direction: column;
        min-width: 0;
        flex: 1;
    }}
    .sidebar.collapsed .user-details {{
        display: none;
    }}
    
    .user-name {{
        font-weight: 700;
        font-size: 0.82rem;
        color: var(--text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    
    .user-email {{
        font-size: 0.7rem;
        color: var(--muted);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    
    .user-menu-dots {{
        color: var(--muted);
        font-size: 0.95rem;
        cursor: pointer;
    }}
    .sidebar.collapsed .user-menu-dots {{
        display: none;
    }}
    
    /* Logout Button */
    .logout-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        height: 48px;
        width: 100%;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        background: transparent;
        color: var(--text);
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none;
        transition: var(--transition);
        cursor: pointer;
    }}
    .logout-btn:hover {{
        background: var(--panel-hover);
        border-color: var(--primary);
    }}
    .logout-btn svg {{
        stroke: var(--text);
        fill: none;
    }}
    .sidebar.collapsed .logout-label {{
        display: none;
    }}

    /* Glassmorphism containers and cards */
    .glass-card {{
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(18px) !important;
        box-shadow: var(--shadow-lg) !important;
        margin-bottom: 1rem !important;
    }}

    /* Native metrics styling overrides */
    div[data-testid="metric-container"] {{
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 1.2rem 1.5rem !important;
        backdrop-filter: blur(18px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    }}
    div[data-testid="metric-container"] label {{
        color: var(--muted) !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.78rem !important;
    }}
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
        font-weight: 800 !important;
        font-size: 1.9rem !important;
        color: var(--text) !important;
        font-family: 'Outfit', sans-serif !important;
    }}

    /* Global inputs and selectboxes */
    div[data-baseweb="select"] > div, input {{
        background-color: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important;
    }}
    div[data-baseweb="select"] > div:hover, input:hover {{
        border-color: var(--primary) !important;
    }}

    /* Tabs Styling */
    button[data-baseweb="tab"] {{
        color: var(--muted) !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--text) !important;
        border-bottom-color: var(--primary) !important;
    }}

    /* Custom scrollbars */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(15, 23, 42, 0.1);
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(255, 255, 255, 0.2);
    }}

    /* Responsive Breakpoints (Appendix H) */
    /* Laptop range: 1024px - 1400px (standard view) */
    @media (max-width: 1400px) and (min-width: 1024px) {{
        .navbar-center {{
            max-width: 420px !important;
        }}
    }}
    
    /* Tablet Range: 768px - 1024px */
    @media (max-width: 1024px) and (min-width: 768px) {{
        .sidebar {{
            width: var(--sidebar-collapsed-width) !important;
            padding: 1.5rem 0.5rem !important;
        }}
        .sidebar .nav-label, .sidebar .sidebar-group-header, .sidebar .user-details, .sidebar .user-menu-dots, .sidebar .logout-label {{
            display: none !important;
        }}
        .sidebar .nav-item {{
            justify-content: center !important;
            padding: 14px 0 !important;
        }}
        .sidebar .user-card {{
            padding: 8px !important;
            justify-content: center !important;
            border: none !important;
            background: transparent !important;
        }}
        .block-container {{
            padding-left: calc(var(--sidebar-collapsed-width) + 24px) !important;
        }}
        .sticky-navbar {{
            padding-left: calc(var(--sidebar-collapsed-width) + 24px) !important;
        }}
    }}
    
    /* Mobile Range: < 768px */
    @media (max-width: 768px) {{
        .sidebar {{
            width: var(--sidebar-width) !important;
            transform: translateX(-100%);
        }}
        .sidebar.active {{
            transform: translateX(0);
        }}
        .block-container {{
            padding-left: 24px !important;
        }}
        .sticky-navbar {{
            padding-left: 24px !important;
        }}
        .navbar-center {{
            display: none !important; /* Hide search bar on mobile headers */
        }}
    }}
    
    .profile-grid {{
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 1rem 1.5rem !important;
    }}
    
    .status-badge {{
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        padding: 2px 8px !important;
        border-radius: 12px !important;
        display: inline-block !important;
    }}
    .status-badge-success {{
        color: var(--green) !important;
        background: rgba(16, 185, 129, 0.1) !important;
    }}
    .status-badge-warning {{
        color: var(--warning) !important;
        background: rgba(245, 158, 11, 0.1) !important;
    }}
    .status-badge-danger {{
        color: var(--red) !important;
        background: rgba(239, 68, 68, 0.1) !important;
    }}

    .play-card {{
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-left: 4px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 1.1rem !important;
        margin-bottom: 0.8rem !important;
        backdrop-filter: blur(18px) !important;
    }}
    .play-card-header {{
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        margin-bottom: 0.4rem !important;
    }}
    .play-card-title {{
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        color: #38bdf8 !important;
    }}

    .health-banner {{
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(18px) !important;
        margin-bottom: 2.0rem !important;
        box-shadow: var(--shadow-lg) !important;
    }}
        .health-banner-danger {{
            background: rgba(239, 68, 68, 0.08) !important;
            border-color: rgba(239, 68, 68, 0.2) !important;
            border-left: 5px solid var(--red) !important;
        }}

        /* --- Navbar Overlays --- */
        /* Disable pointer events on visual links to prevent browser page reloads */
        .settings-nav-link, .search-container {{
            pointer-events: none !important;
        }}

        /* Elevate the parent element-containers of all navbar overlay controls to stack them on top of the visual layout */
        .element-container:has(.st-key-btn_hamburger),
        .element-container:has(.st-key-btn_theme),
        .element-container:has(.st-key-btn_settings_nav),
        .element-container:has(.st-key-search_input_nav) {{
            position: relative !important;
            z-index: 100000 !important;
        }}

        /* Dynamic active button styles inside the native stSidebar */
        .st-key-btn_{active_slug} button {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.22) 0%, rgba(99, 102, 241, 0.08) 100%) !important;
            border: 1px solid rgba(99, 102, 241, 0.35) !important;
            border-left: 3.5px solid var(--primary) !important;
            color: var(--text) !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.12) !important;
        }}

        /* Hover settings overlay button inside profile dropdown */
        .st-key-btn_settings_nav {{
            display: none !important;
            pointer-events: none !important;
        }}

        .element-container:has(.profile-dropdown:hover) ~ .st-key-btn_settings_nav,
        .st-key-btn_settings_nav:hover {{
            display: block !important;
            position: fixed !important;
            top: 108px !important;
            right: 24px !important;
            width: 180px !important;
            height: 36px !important;
            z-index: 100001 !important;
            pointer-events: auto !important;
        }}

        .st-key-btn_settings_nav button {{
            width: 100% !important;
            height: 100% !important;
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            box-shadow: none !important;
        }}
        .st-key-btn_settings_nav button:hover {{
            background: var(--panel-hover) !important;
            color: var(--primary) !important;
        }}

        /* Hamburger overlay button */
        .st-key-btn_hamburger {{
            position: fixed !important;
            top: 20px !important;
            left: {navbar_padding_left} !important;
            width: 32px !important;
            height: 32px !important;
            z-index: 100000 !important;
            pointer-events: auto !important;
            transition: var(--transition) !important;
        }}
        .st-key-btn_hamburger button {{
            width: 100% !important;
            height: 100% !important;
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            box-shadow: none !important;
        }}

        /* Theme toggle overlay button */
        .st-key-btn_theme {{
            position: fixed !important;
            top: 20px !important;
            right: 282px !important; /* matches theme toggle icon */
            width: 32px !important;
            height: 32px !important;
            z-index: 100000 !important;
            pointer-events: auto !important;
        }}
        .st-key-btn_theme button {{
            width: 100% !important;
            height: 100% !important;
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            box-shadow: none !important;
        }}

        /* Search input overlay positioning */
        .st-key-search_input_nav {{
            position: fixed !important;
            top: 18px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 520px !important;
            z-index: 100000 !important;
            height: 36px !important;
        }}
        @media (max-width: 1400px) and (min-width: 1024px) {{
            .st-key-search_input_nav {{
                width: 420px !important;
            }}
        }}
        @media (max-width: 1024px) {{
            .st-key-search_input_nav {{
                display: none !important;
            }}
        }}

        /* Style the inner Streamlit text input to be transparent so we see the original HTML search container behind it */
        .st-key-search_input_nav input {{
            background: transparent !important;
            border: none !important;
            color: var(--text) !important;
            height: 36px !important;
            padding-left: 2.2rem !important;
            padding-right: 5.0rem !important;
            font-size: 0.82rem !important;
            font-family: 'Inter', sans-serif !important;
        }}
        .st-key-search_input_nav label {{
            display: none !important;
        }}
        .st-key-search_input_nav div[data-testid="stInputHelperText"] {{
            display: none !important;
        }}
    </style>
""", unsafe_allow_html=True)


# Initialize session state variables
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"

def logout():
    st.session_state.jwt_token = None
    st.session_state.current_user = None
    st.cache_data.clear()  # Clear cache on logout
    st.rerun()

def check_401(status_code: int):
    """Detects expired or invalid tokens and automatically redirects to the login screen."""
    if status_code == 401:
        st.session_state.jwt_token = None
        st.session_state.current_user = None
        st.cache_data.clear()
        st.toast("Session expired. Please log in again.", icon="🔒")
        time.sleep(1.0)  # brief pause for toast display
        st.rerun()

# --- Caching Layers for In-Memory Performance ---
@st.cache_data(ttl=60)
def cached_get_overview(token: str):
    """Fetches cohort aggregation summary from the API (cached for 60s)."""
    status, data = api_client.get_overview()
    return status, data

@st.cache_data(ttl=60)
def cached_get_save_plays(token: str):
    """Fetches retention plays recommendation data from the API (cached for 60s)."""
    status, data = api_client.get_save_plays()
    return status, data

@st.cache_data(ttl=60)
def cached_get_cohort_data(token: str):
    """Fetches all customer details for cohort analysis (cached for 60s)."""
    status, data = api_client.get_cohort_data()
    return status, data

@st.cache_data(ttl=60)
def cached_get_diagnostics_metadata(token: str):
    """Fetches diagnostics metadata from the API (cached for 60s)."""
    status, data = api_client.get_diagnostics_metadata()
    return status, data

@st.cache_data(ttl=60)
def cached_get_model_health(token: str):
    """Fetches model health and feature drift statistics (cached for 60s)."""
    status, data = api_client.get_model_health()
    return status, data

@st.cache_data(ttl=15, show_spinner=False)
def cached_get_customer_explanation(token: str, customer_id: str):
    """Fetches SHAP force plots, demographics, recommendations and counterfactuals for an ID (cached 15s)."""
    status, data = api_client.get_customer_explanation(customer_id)
    return status, data

# --- Authentication Overlay ---
if st.session_state.jwt_token is None:
    render_auth_view(api_client, primary_color_hex, secondary_color_hex)
    st.stop()

# --- Authenticated App Context ---
# --- Authenticated App Context ---

page = PAGE_MAP[active_slug]

# Make sure session state page is synced
st.session_state.current_page = page

# Setup icons and active highlights for the custom HTML components
def get_active_class(slug):
    return "active" if active_slug == slug else ""

current_search = st.query_params.get("search", "")

# Render Custom Top Sticky Navbar (Appendix B)
st.markdown(f"""<div class="sticky-navbar">
<div class="navbar-left">
<a href="/?page={active_slug}&collapsed={toggle_collapsed_str}&theme={theme}" target="_self" class="nav-icon" style="font-size: 1.25rem;">
<span class="hamburger-menu">☰</span>
</a>
<span class="navbar-logo">Retain<span style="color:#6366f1;">IQ</span></span>
</div>
<div class="navbar-center">
<form action="/" method="get" class="search-container">
<input type="hidden" name="page" value="explorer">
<input type="hidden" name="collapsed" value="{collapsed_str}">
<input type="hidden" name="theme" value="{theme}">
<span class="search-icon">🔍</span>
<input type="text" name="search" class="search-input" placeholder="Search metrics, segments, customers..." value="{current_search}">
<span class="search-badge">Ctrl + K</span>
</form>
</div>
<div class="navbar-right">
<a href="/?page={active_slug}&collapsed={collapsed_str}&theme={'light' if theme == 'dark' else 'dark'}" target="_self" class="nav-icon" title="Toggle Theme">
{ '☀️' if theme == 'light' else '🌙' }
</a>
<div class="notification-dropdown">
<span class="nav-icon">
🔔<span class="notification-badge">3</span>
</span>
<div class="notification-content">
<div class="notification-item" style="font-weight: 700; color: var(--primary);">System Notifications</div>
<div class="notification-item">🚨 Model Drift: Warning detected on commitment score</div>
<div class="notification-item">📤 Data Ingestion: Batch import completed successfully</div>
<div class="notification-item">🔮 Churn Risk: 19 clients flagged as high risk</div>
</div>
</div>
<span class="nav-icon" title="Help & Documentation">❓</span>
<div class="profile-dropdown">
<div class="navbar-profile">
<div class="profile-avatar">AD</div>
<div class="profile-info">
<span class="profile-name">Admin User</span>
<span class="profile-email">admin@retainiq.com</span>
</div>
<span class="profile-arrow">▼</span>
</div>
<div class="profile-content">
<a href="/?page=settings&collapsed={collapsed_str}&theme={theme}" target="_self" class="profile-link settings-nav-link">⚙️ Account Settings</a>
<a href="/?logout=true" target="_self" class="profile-link" style="color: var(--red);">🚪 Sign Out</a>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

# --- Render Native Sidebar Layout ---
with st.sidebar:
    # 1. Navigation group header
    st.markdown('<div class="sidebar-group-header">ANALYTICS</div>', unsafe_allow_html=True)
    
    # 2. Sidebar buttons
    if st.button("📊 Dashboard", key="btn_dashboard", use_container_width=True):
        navigate_to("dashboard")
    if st.button("🔍 Customer Explorer", key="btn_explorer", use_container_width=True):
        navigate_to("explorer")
    if st.button("🔮 Counterfactual Simulator", key="btn_simulator", use_container_width=True):
        navigate_to("simulator")
    if st.button("📈 Analytics", key="btn_analytics", use_container_width=True):
        navigate_to("analytics")
    if st.button("🌍 Explainability", key="btn_explainability", use_container_width=True):
        navigate_to("explainability")
        
    # 3. Spacers and group headers
    st.markdown('<div class="sidebar-group-header">DATA & MODELS</div>', unsafe_allow_html=True)
    if st.button("🧩 Customer Segments", key="btn_segments", use_container_width=True):
        navigate_to("segments")
    if st.button("📤 Upload Dataset", key="btn_upload", use_container_width=True):
        navigate_to("upload")
    if st.button("🩺 Model Diagnostics", key="btn_diagnostics", use_container_width=True):
        navigate_to("diagnostics")
    if st.button("🚨 Drift Detection", key="btn_drift", use_container_width=True):
        navigate_to("drift")
        
    st.markdown('<div class="sidebar-group-header">CONFIGURATION</div>', unsafe_allow_html=True)
    if st.button("⚙️ Settings", key="btn_settings", use_container_width=True):
        navigate_to("settings")
        
    # 4. User profile card (rendered as a static styled block)
    st.markdown("""
        <div class="user-card" style="margin-top: auto; margin-bottom: 12px;">
            <div class="user-avatar">AD</div>
            <div class="user-details">
                <span class="user-name">Admin User</span>
                <span class="user-email">admin@retainiq.com</span>
            </div>
            <span class="user-menu-dots">⋮</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 5. Logout Button
    if st.button("🚪 Log Out", key="btn_logout", use_container_width=True):
        st.query_params["logout"] = "true"
        st.rerun()

# 6. Navbar overlay controls (hamburger, theme, settings_nav, and search)
if st.button("", key="btn_hamburger"):
    toggle_sidebar()

if st.button("", key="btn_theme"):
    toggle_theme()

if st.button("", key="btn_settings_nav"):
    navigate_to("settings")

search_val = st.text_input(
    "Search",
    value=current_search,
    placeholder="Search metrics, segments, customers...",
    label_visibility="collapsed",
    key="search_input_nav"
)
if search_val != current_search:
    st.query_params["page"] = "explorer"
    st.query_params["search"] = search_val
    st.query_params["collapsed"] = "true" if is_collapsed else "false"
    st.query_params["theme"] = theme
    st.rerun()

page = st.session_state.current_page

# Header Section
st.markdown("<div class='main-title'>RetainIQ Churn Portal</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Analyze customer lifetime risk, local explainability drivers, and map targeted Save Plays.</div>", unsafe_allow_html=True)

# Dispatch router
if page == "📊 Dashboard":
    status_code, overview = cached_get_overview(st.session_state.jwt_token)
    check_401(status_code)
    
    if status_code != 200:
        st.error(f"Failed to load overview data from API: {overview.get('detail', 'Unknown error')}")
        st.stop()
        
    _, plays_data_raw = cached_get_save_plays(st.session_state.jwt_token)
    _, cohort_data = cached_get_cohort_data(st.session_state.jwt_token)
    
    render_dashboard_view(
        overview=overview,
        plays_data_raw=plays_data_raw,
        cohort_data=cohort_data or [],
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "🔍 Customer Explorer":
    render_explorer_view(
        api_client=api_client,
        check_401_callback=check_401,
        get_explanation_callback=cached_get_customer_explanation,
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "🔮 Counterfactual Simulator":
    render_counterfactual_view(
        api_client=api_client,
        check_401_callback=check_401,
        get_explanation_callback=cached_get_customer_explanation,
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "📈 Analytics":
    status_code_cohort, cohort_data = cached_get_cohort_data(st.session_state.jwt_token)
    check_401(status_code_cohort)
    
    if status_code_cohort != 200:
        st.error("Failed to load cohort data for Executive Analytics.")
        st.stop()
        
    _, plays_data_raw = cached_get_save_plays(st.session_state.jwt_token)
    
    render_executive_view(
        cohort_data=cohort_data,
        plays_data_raw=plays_data_raw,
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "🌍 Explainability":
    render_explainability_view(
        project_root=project_root,
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "🧩 Customer Segments":
    status_code_cohort, cohort_data = cached_get_cohort_data(st.session_state.jwt_token)
    check_401(status_code_cohort)
    
    if status_code_cohort != 200:
        st.error("Failed to load cohort data for Customer Segments.")
        st.stop()
        
    render_segments_view(
        cohort_data=cohort_data,
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "📤 Upload Dataset":
    render_ingestion_view(
        api_client=api_client,
        check_401_callback=check_401
    )

elif page == "🩺 Model Diagnostics":
    m_status, m_data = cached_get_diagnostics_metadata(st.session_state.jwt_token)
    check_401(m_status)
    
    h_status, health = cached_get_model_health(st.session_state.jwt_token)
    check_401(h_status)
    
    _, cohort_data = cached_get_cohort_data(st.session_state.jwt_token)
    
    render_diagnostics_view(
        diagnostics_metadata=m_data if m_status == 200 else {},
        model_health=health if h_status == 200 else {},
        cohort_data=cohort_data,
        project_root=project_root,
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "🚨 Drift Detection":
    h_status, health = cached_get_model_health(st.session_state.jwt_token)
    check_401(h_status)
    
    render_drift_view(
        model_health=health if h_status == 200 else {},
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )

elif page == "⚙️ Settings":
    render_settings_view(
        primary_color_hex=primary_color_hex,
        secondary_color_hex=secondary_color_hex,
        danger_color_hex=danger_color_hex
    )
