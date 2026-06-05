import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import datetime

@st.cache_resource
def compute_tfidf_matrix(_df):
    """
    Computes and caches the TF-IDF matrix. We concatenate text fields
    to create a content-rich feature soup.
    """
    # Fill nulls and join features
    soup = (
        _df['type'].fillna('') + " " +
        _df['listed_in'].fillna('') + " " +
        _df['director'].fillna('') + " " +
        _df['cast'].fillna('') + " " +
        _df['country'].fillna('') + " " +
        _df['description'].fillna('')
    )
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
    tfidf_matrix = vectorizer.fit_transform(soup)
    return tfidf_matrix, vectorizer

def log_interaction(db_conn, show_id, title, action_type="view"):
    """Logs user interactions to the database."""
    if db_conn is None:
        return
    try:
        cursor = db_conn.cursor()
        query = """
            INSERT INTO user_interactions (show_id, title, action_type, interaction_time)
            VALUES (%s, %s, %s, %s)
        """
        # SQLite uses '?' instead of '%s', so we must adapt based on connection type
        import sqlite3
        if isinstance(db_conn, sqlite3.Connection):
            query = query.replace("%s", "?")
            
        cursor.execute(query, (show_id, title, action_type, datetime.datetime.now()))
        db_conn.commit()
        cursor.close()
    except Exception as e:
        # Silently fail or log to streamlit debug
        pass

def log_recommendation_search(db_conn, search_method, query_params, num_results):
    """Logs recommendation searches to the database."""
    if db_conn is None:
        return
    try:
        cursor = db_conn.cursor()
        query = """
            INSERT INTO recommendation_logs (search_method, query_parameters, results_count, search_time)
            VALUES (%s, %s, %s, %s)
        """
        import sqlite3
        if isinstance(db_conn, sqlite3.Connection):
            query = query.replace("%s", "?")
            
        cursor.execute(query, (search_method, str(query_params), int(num_results), datetime.datetime.now()))
        db_conn.commit()
        cursor.close()
    except Exception as e:
        pass

def show_recommendations(df, db_conn):
    # Top AI Badge
    st.markdown(
        """
        <div style="display: inline-flex; align-items: center; gap: 6px; border: 1px solid rgba(229, 9, 20, 0.45); background: rgba(229, 9, 20, 0.12); color: #ff3e4e; font-size: 11px; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-family: 'Orbitron', sans-serif; text-transform: uppercase; margin-bottom: 15px;">
            <span style="color: #ff3e4e; font-size: 12px; margin-right: 2px;">✨</span> AI ENGINE ACTIVE
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Styled Serif Title and description matching screenshot
    st.markdown(
        """
        <h1 style="font-family: 'Playfair Display', 'Georgia', serif; font-style: italic; font-weight: 700; color: #ffffff; font-size: 3.2rem; margin: 0 0 12px 0; letter-spacing: -0.5px; text-shadow: 0 4px 10px rgba(0,0,0,0.5);">
            Smart Recommendation Engine
        </h1>
        <p style="color: #a0a0a5; font-size: 1.15rem; line-height: 1.6; max-width: 800px; margin-bottom: 35px;">
            Discover your next obsession. Our AI analyzes genre trends, content ratings, and viewership semantics to suggest titles you'll love.
        </p>
        """,
        unsafe_allow_html=True
    )

    # Initialize TF-IDF matrix
    with st.spinner("Initializing AI Recommendation Matrix..."):
        tfidf_matrix, _ = compute_tfidf_matrix(df)

    # Initialize session states to persist search results on button click reruns
    if "filter_results" not in st.session_state:
        st.session_state.filter_results = None
    if "filter_show_all" not in st.session_state:
        st.session_state.filter_show_all = False
    if "ml_results" not in st.session_state:
        st.session_state.ml_results = None
    if "ml_base_title" not in st.session_state:
        st.session_state.ml_base_title = ""

    # ----------------------------------------------------
    # SECTION 1: ATTRIBUTE-BASED CATALOG FILTER (SCREENSHOT LAYOUT)
    # ----------------------------------------------------
    with st.container():
        st.markdown('<div class="smart-engine-anchor"></div>', unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("<label class='smart-label'>GENRE CATEGORY</label>", unsafe_allow_html=True)
            all_genres = sorted(list(set(df['listed_in'].str.split(', ').explode())))
            genre_options = ["All Genres"] + all_genres
            sel_genre = st.selectbox("Genre Select", genre_options, label_visibility="collapsed")
            
        with col_f2:
            st.markdown("<label class='smart-label'>🎬 CONTENT FORMAT</label>", unsafe_allow_html=True)
            sel_type = st.selectbox("Format Select", ["All Formats", "Movie", "TV Show"], label_visibility="collapsed")
            
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        col_f3, col_f4 = st.columns(2)
        with col_f3:
            st.markdown("<label class='smart-label'>📅 RELEASE ERA</label>", unsafe_allow_html=True)
            era_options = ["All Years", "New Releases (2020-Present)", "Golden Era (2010-2019)", "Classic Era (Before 2010)"]
            sel_era = st.selectbox("Era Select", era_options, label_visibility="collapsed")
            
        with col_f4:
            st.markdown("<label class='smart-label'>⭐ CONTENT RATING</label>", unsafe_allow_html=True)
            all_ratings = sorted(list(df['rating'].dropna().unique()))
            rating_options = ["All Ratings"] + all_ratings
            sel_rating = st.selectbox("Rating Select", rating_options, label_visibility="collapsed")
            
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        apply_filters = st.button("✨ Generate Smart Picks", key="generate_smart_picks", use_container_width=True)

    # Show all toggle below box
    show_all = st.checkbox("Show all matching titles (Default shows top 10)", value=st.session_state.filter_show_all)

    # Process filter action
    if apply_filters:
        filtered_df = df.copy()
        
        # Genre category filter
        if sel_genre != "All Genres":
            # Filter rows where genre exists in listed_in column
            filtered_df = filtered_df[filtered_df['listed_in'].str.contains(sel_genre, case=False, na=False)]
            
        # Content format filter
        if sel_type != "All Formats":
            filtered_df = filtered_df[filtered_df['type'] == sel_type]
            
        # Release era filter
        if sel_era == "New Releases (2020-Present)":
            filtered_df = filtered_df[filtered_df['release_year'] >= 2020]
        elif sel_era == "Golden Era (2010-2019)":
            filtered_df = filtered_df[(filtered_df['release_year'] >= 2010) & (filtered_df['release_year'] <= 2019)]
        elif sel_era == "Classic Era (Before 2010)":
            filtered_df = filtered_df[filtered_df['release_year'] < 2010]
            
        # Content rating filter
        if sel_rating != "All Ratings":
            filtered_df = filtered_df[filtered_df['rating'] == sel_rating]
            
        filtered_df = filtered_df.sort_values(by="release_year", ascending=False)
        
        # Save to session state
        st.session_state.filter_results = filtered_df
        st.session_state.filter_show_all = show_all
        
        # Log filter query to database
        log_recommendation_search(db_conn, "Multi-Attribute Filter", {
            "genre": sel_genre, "type": sel_type, "era": sel_era, "rating": sel_rating
        }, len(filtered_df))

    # Render filter results
    if st.session_state.filter_results is not None:
        filtered_df = st.session_state.filter_results
        show_all = st.session_state.filter_show_all
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 🔎 Filter Results ({len(filtered_df)} matches found)")
        
        if filtered_df.empty:
            st.warning("No titles match your selection options. Try widening your criteria.")
        else:
            display_df = filtered_df if show_all else filtered_df.head(10)
            
            for _, row in display_df.iterrows():
                # Beautiful card layout matching user screenshot
                st.markdown(f"""
                <div class="movie-desc-card">
                    <div class="movie-card-thumb">
                        <svg class="play-icon" viewBox="0 0 24 24" fill="none" stroke="#e50914" stroke-width="2" stroke-linejoin="round">
                            <polygon points="6 3 20 12 6 21 6 3"></polygon>
                        </svg>
                    </div>
                    <div class="movie-card-content">
                        <div class="movie-card-header">
                            <h3 class="movie-card-title">{row['title']}</h3>
                            <span class="movie-card-format">{row['type']}</span>
                        </div>
                        <div class="movie-card-meta">
                            <span style="margin-right: 15px;">📅 {row['release_year']}</span>
                            <span style="color: #ffc107; font-weight: bold;">⭐ {row['rating']}</span>
                        </div>
                        <p class="movie-card-desc">{row['description']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Dynamic logger button
                if st.button("Log View Activity", key=f"filter_view_{row['show_id']}", use_container_width=True):
                    log_interaction(db_conn, row['show_id'], row['title'], "view_filter_rec")
                    st.success(f"Interaction logged for {row['title']}!")
    
    st.markdown("<br><hr style='border-color: rgba(229, 9, 20, 0.15);'><br>", unsafe_allow_html=True)
    
    # ----------------------------------------------------
    # SECTION 2: COSINE SIMILARITY (ML) MODEL
    # ----------------------------------------------------
    st.markdown("## 🤖 2. Vector-Similarity Matcher (ML)")
    st.markdown("<p style='color: #8a8a93;'>Select a title to run cosine similarity matching based on plots, genres, and cast feature vectors.</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="ml-engine-anchor"></div>', unsafe_allow_html=True)
        
        # Dropdown for title selection
        all_titles = sorted(df['title'].tolist())
        default_index = all_titles.index("Stranger Things") if "Stranger Things" in all_titles else 0
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("<label class='smart-label'>BASE MOVIE OR SHOW</label>", unsafe_allow_html=True)
            selected_title = st.selectbox("Search Base Title Select", all_titles, index=default_index, label_visibility="collapsed")
        with col_m2:
            st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True) # Spacer
            generate_ml = st.button("✨ Match Similar Content", key="generate_ml_picks", use_container_width=True)
    
    # Process ML matching action
    if generate_ml:
        idx_list = df[df['title'] == selected_title].index
        if len(idx_list) > 0:
            idx = idx_list[0]
            query_vector = tfidf_matrix[idx]
            
            # Compute Cosine Similarity scores
            similarity_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
            
            # Exclude base title (self) and fetch top 5 recommendations
            top_indices = similarity_scores.argsort()[-6:-1][::-1]
            
            recs_df = df.iloc[top_indices].copy()
            recs_df['score'] = similarity_scores[top_indices]
            
            # Save to session state
            st.session_state.ml_results = recs_df
            st.session_state.ml_base_title = selected_title
            
            # Log ML query to database
            log_recommendation_search(db_conn, "ML Cosine Similarity", {"title": selected_title}, len(recs_df))
        else:
            st.error("Title not found in dataset matrix.")
            
    # Render ML results
    if st.session_state.ml_results is not None:
        recs_df = st.session_state.ml_results
        ml_title = st.session_state.ml_base_title
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 🛰️ Content Matches for **{ml_title}**")
        
        # Display results in structured glass panels with descriptions
        for _, row in recs_df.iterrows():
            sim_pct = int(row['score'] * 100)
            
            st.markdown(f"""
            <div class="movie-desc-card">
                <div class="movie-card-thumb">
                    <svg class="play-icon" viewBox="0 0 24 24" fill="none" stroke="#e50914" stroke-width="2" stroke-linejoin="round">
                        <polygon points="6 3 20 12 6 21 6 3"></polygon>
                    </svg>
                </div>
                <div class="movie-card-content">
                    <div class="movie-card-header">
                        <h3 class="movie-card-title">{row['title']}</h3>
                        <span class="movie-card-format">{row['type']}</span>
                    </div>
                    <div class="movie-card-meta">
                        <span style="margin-right: 15px; color: #ff3e4e; font-family: 'Orbitron'; font-weight: bold;">🛰️ {sim_pct}% MATCH</span>
                        <span style="margin-right: 15px;">📅 {row['release_year']}</span>
                        <span style="color: #ffc107; font-weight: bold;">⭐ {row['rating']}</span>
                    </div>
                    <p class="movie-card-desc">{row['description']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Interaction logger button
            if st.button("Log View Activity", key=f"ml_view_{row['show_id']}", use_container_width=True):
                log_interaction(db_conn, row['show_id'], row['title'], "view_ml_rec")
                st.success(f"Interaction logged for {row['title']}!")
