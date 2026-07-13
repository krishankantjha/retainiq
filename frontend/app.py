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

st.set_page_config(
    page_title="RetainIQ — Customer Churn Dashboard",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Parse routing and layout parameters from query params
if st.query_params.get("logout") == "true":
    st.query_params.clear()
    st.session_state.jwt_token = None
    st.session_state.current_user = None
    st.cache_data.clear()
    st.rerun()

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

# Sidebar collapse setup
is_collapsed = (st.query_params.get("collapsed") == "true")
collapsed_str = "true" if is_collapsed else "false"
toggle_collapsed_str = "false" if is_collapsed else "true"
collapsed_class = "collapsed" if is_collapsed else ""

# Main content and navbar paddings
# If the user is not authenticated, do not offset the main container for the sidebar/navbar
if st.session_state.get("jwt_token") is None:
    content_padding_left = "2.5rem"
    navbar_padding_left = "2.5rem"
    padding_top = "2.5rem"
else:
    padding_top = "calc(var(--navbar-height) + 1.5rem)"
    if is_collapsed:
        content_padding_left = "calc(var(--sidebar-collapsed-width) + 24px)"
        navbar_padding_left = "calc(var(--sidebar-collapsed-width) + 24px)"
    else:
        content_padding_left = "calc(var(--sidebar-width) + 24px)"
        navbar_padding_left = "calc(var(--sidebar-width) + 24px)"

# Mobile side overlay menu setup
is_menu_open = (st.query_params.get("menu_open") == "true")
menu_open_str = "true" if is_menu_open else "false"
toggle_menu_open_str = "false" if is_menu_open else "true"
menu_class = "active" if is_menu_open else ""

# Search handling
if "search" in st.query_params:
    st.session_state.explorer_search_input = st.query_params.get("search")

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
    [data-testid="stSidebar"] {{
        display: none !important;
        width: 0 !important;
    }}
    [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
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
    .health-banner-success {{
        background: rgba(16, 185, 129, 0.08) !important;
        border-color: rgba(16, 185, 129, 0.2) !important;
        border-left: 5px solid var(--green) !important;
    }}
    .health-banner-warning {{
        background: rgba(245, 158, 11, 0.08) !important;
        border-color: rgba(245, 158, 11, 0.2) !important;
        border-left: 5px solid var(--warning) !important;
    }}
    .health-banner-danger {{
        background: rgba(239, 68, 68, 0.08) !important;
        border-color: rgba(239, 68, 68, 0.2) !important;
        border-left: 5px solid var(--red) !important;
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

# Define page mapping configuration for routing (Appendix I / J)
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

# Resolve current page parameter from URL
active_slug = st.query_params.get("page", "dashboard")
if active_slug not in PAGE_MAP:
    active_slug = "dashboard"
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
<a href="/?page=settings&collapsed={collapsed_str}&theme={theme}" target="_self" class="profile-link">⚙️ Account Settings</a>
<a href="/?logout=true" target="_self" class="profile-link" style="color: var(--red);">🚪 Sign Out</a>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

# Render Custom HTML Sidebar (Appendix C & D & G)
# Define SVG path strings for sidebar icons
svg_home = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>'
svg_search = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
svg_sliders = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>'
svg_chart = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
svg_eye = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
svg_grid = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
svg_upload = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polyline points="16 16 12 12 8 16"></polyline><line x1="12" y1="12" x2="12" y2="21"></line><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path></svg>'
svg_activity = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>'
svg_triangle = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
svg_settings = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'
svg_logout = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>'

st.markdown(f"""<div class="sidebar {collapsed_class} {menu_class}">
<div class="sidebar-menu">
<div class="sidebar-group-header">ANALYTICS</div>
<a href="/?page=dashboard&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('dashboard')}">
{svg_home}
<span class="nav-label">Dashboard</span>
</a>
<a href="/?page=explorer&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('explorer')}">
{svg_search}
<span class="nav-label">Customer Explorer</span>
</a>
<a href="/?page=simulator&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('simulator')}">
{svg_sliders}
<span class="nav-label">Counterfactual Simulator</span>
</a>
<a href="/?page=analytics&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('analytics')}">
{svg_chart}
<span class="nav-label">Analytics</span>
</a>
<a href="/?page=explainability&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('explainability')}">
{svg_eye}
<span class="nav-label">Explainability</span>
</a>
<div class="sidebar-group-header">DATA & MODELS</div>
<a href="/?page=segments&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('segments')}">
{svg_grid}
<span class="nav-label">Customer Segments</span>
</a>
<a href="/?page=upload&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('upload')}">
{svg_upload}
<span class="nav-label">Upload Dataset</span>
</a>
<a href="/?page=diagnostics&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('diagnostics')}">
{svg_activity}
<span class="nav-label">Model Diagnostics</span>
</a>
<a href="/?page=drift&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('drift')}">
{svg_triangle}
<span class="nav-label">Drift Detection</span>
</a>
<div class="sidebar-group-header">CONFIGURATION</div>
<a href="/?page=settings&collapsed={collapsed_str}&theme={theme}" target="_self" class="nav-item {get_active_class('settings')}">
{svg_settings}
<span class="nav-label">Settings</span>
</a>
</div>
<div class="user-card">
<div class="user-avatar">AD</div>
<div class="user-details">
<span class="user-name">Admin User</span>
<span class="user-email">admin@retainiq.com</span>
</div>
<span class="user-menu-dots">⋮</span>
</div>
<a href="/?logout=true" target="_self" class="logout-btn">
{svg_logout}
<span class="logout-label">Log Out</span>
</a>
</div>""", unsafe_allow_html=True)

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
