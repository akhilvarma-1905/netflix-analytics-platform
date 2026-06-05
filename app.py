import streamlit as st
import pandas as pd
import os
import base64
import psycopg2

# Import page modules
from pages.analytics import show_analytics
from pages.recommendations import show_recommendations
from pages.insights import show_insights, show_ai_assistant_page
from pages.about import show_about

# ------------------ STREAMLIT SETTINGS ------------------
st.set_page_config(
    page_title="Netflix Analytics & Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Mobile viewport (ensures correct scaling on phones/tablets)
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
    """,
    unsafe_allow_html=True,
)

# ------------------ CSS STYLESHEET INJECTION ------------------
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"Styles file {file_name} not found.")

# Inject Custom 3D Cyber Theme CSS
local_css("style.css")

# ------------------ DATABASE CONFIGURATION ------------------
db_host = os.getenv("DB_HOST", "localhost")
db_user = os.getenv("DB_USER", "postgres")
db_pass = os.getenv("DB_PASSWORD", "1234")
db_db = os.getenv("DB_NAME", "netflix_project")
db_port = int(os.getenv("DB_PORT", "5432"))

# ------------------ DATABASE INITIATOR ------------------
def init_db(host, user, password, db_name, port=5432):
    """
    Initializes the PostgreSQL database schema if tables are missing.
    Returns connection object.
    """
    try:
        # Connect to postgres db to create db_name if not exists
        conn_temp = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            dbname="postgres"
        )
        conn_temp.autocommit = True
        cursor = conn_temp.cursor()
        
        # Check database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.close()
        conn_temp.close()
        
        # Connect to target database
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port=port
        )
        
        # Schema Setup
        cursor = conn.cursor()
        
        # 1. Netflix catalog metadata table
        create_netflix_table = """
        CREATE TABLE IF NOT EXISTS netflix (
            show_id VARCHAR(10) PRIMARY KEY,
            type VARCHAR(20),
            title VARCHAR(255),
            director TEXT,
            "cast" TEXT,
            country VARCHAR(150),
            date_added VARCHAR(50),
            release_year INT,
            rating VARCHAR(15),
            duration VARCHAR(30),
            listed_in TEXT,
            description TEXT,
            year_added INT
        )
        """
        cursor.execute(create_netflix_table)
        
        # 2. User Detail Click interactions logs table
        create_interactions_table = """
        CREATE TABLE IF NOT EXISTS user_interactions (
            interaction_id SERIAL PRIMARY KEY,
            show_id VARCHAR(10),
            title VARCHAR(255),
            action_type VARCHAR(50),
            interaction_time TIMESTAMP
        )
        """
        cursor.execute(create_interactions_table)
        
        # 3. Recommendation Search queries logs table
        create_logs_table = """
        CREATE TABLE IF NOT EXISTS recommendation_logs (
            log_id SERIAL PRIMARY KEY,
            search_method VARCHAR(50),
            query_parameters TEXT,
            results_count INT,
            search_time TIMESTAMP
        )
        """
        cursor.execute(create_logs_table)
        conn.commit()
        cursor.close()
        
        return conn
    except Exception as e:
        st.error(f"PostgreSQL Database / Schema Setup Failed: {str(e)}")
        return None

db_conn = init_db(db_host, db_user, db_pass, db_db, db_port)

# ------------------ DATA LOADING (CACHED FROM POSTGRESQL / CSV FALLBACK) ------------------
def load_fallback_csv(csv_path):
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            # Map column names if they differ
            if "cast_members" in df.columns and "cast" not in df.columns:
                df = df.rename(columns={"cast_members": "cast"})
            elif "cast" in df.columns and "cast_members" not in df.columns:
                df["cast_members"] = df["cast"]
                
            required_cols = ["show_id", "type", "title", "director", "cast", "country", "date_added", "release_year", "rating", "duration", "listed_in", "description", "year_added"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = "Unknown"
                    
            df['director'] = df['director'].fillna('Unknown')
            df['cast'] = df['cast'].fillna('Unknown')
            df['country'] = df['country'].fillna('Unknown')
            df['date_added'] = df['date_added'].fillna('Unknown')
            df['rating'] = df['rating'].fillna('TV-MA')
            df['duration'] = df['duration'].fillna('Unknown')
            df['year_added'] = df['year_added'].fillna(2021)
            try:
                df['year_added'] = df['year_added'].astype(int)
            except Exception:
                pass
            return df[required_cols]
        else:
            st.error(f"Fallback CSV file not found at: {csv_path}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to load fallback CSV: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=2)
def load_postgres_data():
    try:
        cursor = db_conn.cursor()
        cursor.execute('SELECT show_id, type, title, director, cast_members AS "cast", country, date_added, release_year, rating, duration, listed_in, description, year_added FROM netflix')
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        df = pd.DataFrame(rows, columns=columns)
        df['director'] = df['director'].fillna('Unknown')
        df['cast'] = df['cast'].fillna('Unknown')
        df['country'] = df['country'].fillna('Unknown')
        df['date_added'] = df['date_added'].fillna('Unknown')
        df['rating'] = df['rating'].fillna('TV-MA')
        df['duration'] = df['duration'].fillna('Unknown')
        df['year_added'] = df['year_added'].fillna(2021).astype(int)
        return df, False
    except Exception as e:
        return pd.DataFrame(), True

# Attempt to load data with fallback
is_fallback = False
csv_local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netflix_psql.csv")
if db_conn is None:
    is_fallback = True
    df_data = load_fallback_csv(csv_local_path)
else:
    df_data, is_fallback = load_postgres_data()
    if is_fallback or df_data.empty:
        is_fallback = True
        df_data = load_fallback_csv(csv_local_path)

if "is_db_fallback" not in st.session_state:
    st.session_state.is_db_fallback = is_fallback
else:
    st.session_state.is_db_fallback = is_fallback


# ------------------ IMAGE HELPER ------------------
def get_image_as_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return ""

# ------------------ SPA PAGES ROUTING SYSTEM ------------------
# Save previous page before page query param updates active page
if "page" in st.query_params:
    new_page = st.query_params["page"]
    if "page" in st.session_state and st.session_state.page != "AI_Assistant":
        st.session_state.prev_page = st.session_state.page
    st.session_state.page = new_page

# Navigation Session State
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "prev_page" not in st.session_state:
    st.session_state.prev_page = "Home"

# Update previous page tracker when navigating within the app via session state
if st.session_state.page != "AI_Assistant":
    st.session_state.prev_page = st.session_state.page

def navigate_to(page_name):
    if st.session_state.page != "AI_Assistant":
        st.session_state.prev_page = st.session_state.page
    st.session_state.page = page_name
    st.query_params["page"] = page_name


# ------------------ PERSISTENT NAVBAR ------------------
if not st.session_state.get("zoho_fullscreen", False) and st.session_state.page != "AI_Assistant":
    active_home = "active" if st.session_state.page == "Home" else ""
    active_analytics = "active" if st.session_state.page == "Analytics" else ""
    active_recs = "active" if st.session_state.page == "Recommendations" else ""
    active_insights = "active" if st.session_state.page == "Insights" else ""
    active_about = "active" if st.session_state.page == "About" else ""
    
    navbar_html = f"""
    <div class="cyber-navbar">
        <a href="?page=Home" target="_self" class="nav-brand">
            <div class="brand-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 5V19L19 12L8 5Z" fill="white"/>
                </svg>
            </div>
            <span class="brand-text">Netflix <span>Analytics</span></span>
        </a>
        <div class="nav-links-scroll">
            <div class="nav-links">
                <a href="?page=Home" target="_self" class="nav-link-item {active_home}">Home</a>
                <a href="?page=Analytics" target="_self" class="nav-link-item {active_analytics}">Analytics</a>
                <a href="?page=Recommendations" target="_self" class="nav-link-item {active_recs}">Recommendations</a>
                <a href="?page=Insights" target="_self" class="nav-link-item {active_insights}">Insights</a>
                <a href="?page=About" target="_self" class="nav-link-item {active_about}">About</a>
            </div>
        </div>
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)

# ------------------ DATABASE FALLBACK STATUS BANNER ------------------
if not st.session_state.get("zoho_fullscreen", False):
    if db_conn is None or st.session_state.get("is_db_fallback", False):
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; background: rgba(229, 9, 20, 0.12); border: 1px solid rgba(229, 9, 20, 0.4); padding: 12px 18px; border-radius: 12px; margin-top: 10px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.15);">
                <span style="font-size: 18px;">⚠️</span>
                <div style="font-size: 13.5px; color: #f5f5f7; font-family: 'Inter', sans-serif; line-height: 1.4;">
                    <strong style="color: #ff3e4e; font-family: 'Orbitron', sans-serif;">DATABASE OFFLINE:</strong> Running in local fallback mode. Active dataset loaded from <code>netflix_psql.csv</code>.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ------------------ MAIN ROUTER CONTENT RENDER ------------------


if st.session_state.page == "Home":
    # Background Image CSS Injection (using Base64 for local images)
    bg_base64 = get_image_as_base64("assets/background.jpg")
    if bg_base64:
        st.markdown(f"""
            <style>
            [data-testid="stAppViewContainer"]::before {{
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: linear-gradient(rgba(8, 8, 10, 0.78), rgba(8, 8, 10, 0.95)), url("data:image/jpeg;base64,{bg_base64}");
                background-size: cover;
                background-position: center;
                z-index: -1;
                opacity: 0.55;
                animation: panBackground 20s infinite alternate ease-in-out;
            }}
            
            @keyframes panBackground {{
                0% {{
                    background-position: 50% 50%;
                    transform: scale(1);
                }}
                100% {{
                    background-position: 52% 48%;
                    transform: scale(1.05);
                }}
            }}
            </style>
        """, unsafe_allow_html=True)

    # Hero Content matching screenshot with a 3D rotating N logo
    hero_html = """
    <div class="hero-wrapper">
        <div class="rotating-logo-container">
            <div class="rotating-logo">
                <svg class="netflix-n-svg" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20,10 L40,10 L40,110 L20,110 Z" fill="#b20710" />
                    <path d="M60,10 L80,10 L80,110 L60,110 Z" fill="#b20710" />
                    <path d="M20,10 L40,10 L80,110 L60,110 Z" fill="url(#diagonal-gradient)" filter="url(#shadow)" />
                    <defs>
                        <linearGradient id="diagonal-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#e50914" />
                            <stop offset="100%" stop-color="#7f050b" />
                        </linearGradient>
                        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                            <feDropShadow dx="-4" dy="4" stdDeviation="5" flood-color="#000000" flood-opacity="0.8"/>
                        </filter>
                    </defs>
                </svg>
            </div>
            <div class="logo-glow-ring"></div>
        </div>
        <div class="hero-badge">
            <span>✨</span> Data-driven content intelligence
        </div>
        <h1 class="hero-title">Netflix Analytics and Recommendation System</h1>
        <p class="hero-subtitle">
            Transform raw Netflix data into actionable insights with advanced analytics, intelligent recommendations, and comprehensive business intelligence tools.
        </p>
        <div class="hero-buttons">
            <a href="?page=Analytics" target="_self" class="hero-btn-primary">
                Explore analytics <span style="margin-left: 8px;">&rarr;</span>
            </a>
            <a href="?page=About" target="_self" class="hero-btn-secondary">
                Learn more
            </a>
        </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)

elif st.session_state.page == "Analytics":
    show_analytics(df_data, db_conn)

elif st.session_state.page == "Recommendations":
    show_recommendations(df_data, db_conn)

elif st.session_state.page == "Insights":
    show_insights(df_data, db_conn)

elif st.session_state.page == "About":
    show_about()

elif st.session_state.page == "AI_Assistant":
    prev_page = st.session_state.get("prev_page", "Home")
    exit_html = f"""
    <div class="ai-exit-container">
        <a href="?page={prev_page}" target="_self" class="ai-exit-button">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; vertical-align: middle;">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            Exit Assistant
        </a>
    </div>
    """
    st.markdown(exit_html, unsafe_allow_html=True)
    show_ai_assistant_page(df_data, db_conn)

# ------------------ FOOTER ------------------
if not st.session_state.get("zoho_fullscreen", False) and st.session_state.page != "AI_Assistant":
    st.markdown("<br><hr style='border-color: rgba(229, 9, 20, 0.15);'><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; color: #55555d; font-size: 12px; font-family: 'Orbitron'; letter-spacing: 0.5px; padding-bottom: 20px;">
            Designed and Engineered with Streamlit, Plotly, & PostgreSQL Connection. 🎬 Netflix Analytics © 2026.
        </div>
    """, unsafe_allow_html=True)

# ------------------ FLOATING AI ASSISTANT BUTTON ------------------
if not st.session_state.get("zoho_fullscreen", False) and st.session_state.page != "AI_Assistant":
    ai_btn_html = """
    <a href="?page=AI_Assistant" target="_self" class="ai-float-button">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <!-- Robot Head Outline -->
            <rect x="3" y="6" width="18" height="14" rx="3" stroke="currentColor" fill="none"></rect>
            <!-- Antenna -->
            <path d="M12 6V3M10 2h4" stroke="currentColor"></path>
            <!-- Eyes -->
            <circle cx="8.5" cy="12.5" r="1.5" fill="currentColor" stroke="none"></circle>
            <circle cx="15.5" cy="12.5" r="1.5" fill="currentColor" stroke="none"></circle>
            <!-- Mouth -->
            <path d="M9.5 16h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
            <!-- Ears -->
            <path d="M2 11h1M21 11h1" stroke="currentColor"></path>
        </svg>
    </a>
    """
    st.markdown(ai_btn_html, unsafe_allow_html=True)

