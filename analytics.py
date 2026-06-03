import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_analytics(df, db_conn):
    # Initialize full screen session state
    if "zoho_fullscreen" not in st.session_state:
        st.session_state.zoho_fullscreen = False
        
    if st.session_state.zoho_fullscreen:
        # Full screen view: hide header navbar and set full-width layout
        st.markdown(
            """
            <style>
            .cyber-navbar {
                display: none !important;
            }
            div.block-container {
                padding-top: 15px !important;
                max-width: 100% !important;
                padding-left: 15px !important;
                padding-right: 15px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Header with side-by-side title and Exit button
        col_fs_h, col_fs_btn = st.columns([9, 2])
        with col_fs_h:
            st.markdown("<h2 class='glowing-title neon-text-red' style='margin: 0; text-align: left;'>🖥️ ZOHO BUSINESS INTELLIGENCE HUB</h2>", unsafe_allow_html=True)
        with col_fs_btn:
            if st.button("🔴 Exit Fullscreen", key="exit_zoho_fs_top", use_container_width=True):
                st.session_state.zoho_fullscreen = False
                st.rerun()
                
        # Immersive dashboard container styled as a floating frame with nested iframe
        st.markdown(
            """
            <div class='floating-dashboard-frame' style='height: 82vh; margin-top: 10px;'>
                <iframe frameborder="0" width="100%" height="100%" style="height: 79vh; border: none; border-radius: 12px;" src="https://analytics.zoho.in/open-view/508314000000005131" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    st.markdown("<h1 class='glowing-title neon-text-red' style='text-align: center; margin-bottom: 20px;'>DATAVERSE ANALYTICS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8a8a93; margin-bottom: 40px;'>Explore content distribution, trends, ratings, and industry projections powered by Zoho & Custom ML engines.</p>", unsafe_allow_html=True)
    
    # ------------------ KPI CARDS ------------------
    st.markdown("### 📊 Platform Metrics Overview")
    
    total_titles = len(df)
    movies_count = len(df[df['type'] == 'Movie'])
    tv_shows = len(df[df['type'] == 'TV Show'])
    avg_year = int(df['release_year'].mean())
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.markdown(f"""
        <div class="stat-card">
            <p style="margin: 0; color: #8a8a93; font-size: 12px; font-weight: bold; text-transform: uppercase;">Total Titles</p>
            <h2 style="margin: 5px 0 0 0; color: #ffffff; font-family: 'Orbitron';">{total_titles:,}</h2>
            <p style="margin: 5px 0 0 0; color: #e50914; font-size: 11px;">★ Active Database</p>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
        <div class="stat-card">
            <p style="margin: 0; color: #8a8a93; font-size: 12px; font-weight: bold; text-transform: uppercase;">Movies Available</p>
            <h2 style="margin: 5px 0 0 0; color: #ffffff; font-family: 'Orbitron';">{movies_count:,}</h2>
            <p style="margin: 5px 0 0 0; color: #e50914; font-size: 11px;">🎬 {int(movies_count/total_titles*100)}% of Catalog</p>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
        <div class="stat-card">
            <p style="margin: 0; color: #8a8a93; font-size: 12px; font-weight: bold; text-transform: uppercase;">TV Shows Available</p>
            <h2 style="margin: 5px 0 0 0; color: #ffffff; font-family: 'Orbitron';">{tv_shows:,}</h2>
            <p style="margin: 5px 0 0 0; color: #e50914; font-size: 11px;">📺 {int(tv_shows/total_titles*100)}% of Catalog</p>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi4:
        st.markdown(f"""
        <div class="stat-card">
            <p style="margin: 0; color: #8a8a93; font-size: 12px; font-weight: bold; text-transform: uppercase;">Avg Release Year</p>
            <h2 style="margin: 5px 0 0 0; color: #ffffff; font-family: 'Orbitron';">{avg_year}</h2>
            <p style="margin: 5px 0 0 0; color: #e50914; font-size: 11px;">📈 Trend Baseline</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ------------------ CHARTS SECTION ------------------
    st.markdown("### 📈 Interactive Distributions")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.write("#### 🎥 Content Type Distribution")
        type_counts = df['type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        fig_type = px.pie(
            type_counts, 
            values='Count', 
            names='Type', 
            color='Type',
            color_discrete_map={'Movie': '#e50914', 'TV Show': '#1a1a24'},
            hole=0.4
        )
        fig_type.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f5f5f7',
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_type, use_container_width=True)
        story_html = """<div class="story-card">
<div class="story-header">
<svg viewBox="0 0 24 24" width="16" height="16" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
Content Split Insights
</div>
<p class="story-body">
Standalone movies represent over <strong>70%</strong> of Netflix's catalog. Netflix utilizes movies to capture quick, low-friction initial views, while using longer TV series (approx. <strong>30%</strong>) to lock in subscribers and secure long-term subscriber retention.
</p>
</div>"""
        st.markdown(story_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.write("#### 🌟 Top 10 Rating Categories")
        rating_counts = df['rating'].value_counts().head(10).reset_index()
        rating_counts.columns = ['Rating', 'Count']
        fig_rating = px.bar(
            rating_counts,
            x='Count',
            y='Rating',
            orientation='h',
            color='Count',
            color_continuous_scale=['#1a1a24', '#e50914']
        )
        fig_rating.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f5f5f7',
            coloraxis_showscale=False,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        fig_rating.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig_rating, use_container_width=True)
        story_html = """<div class="story-card">
<div class="story-header">
<svg viewBox="0 0 24 24" width="16" height="16" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
Target Demographic Insights
</div>
<p class="story-body">
Age-rating certifications like <strong>TV-MA</strong> (Mature Audiences) and <strong>TV-14</strong> (Parents Cautioned) dominate the platform. This demonstrates Netflix's deliberate content alignment towards mature teenagers and adults, steering high-budget productions into complex dramas, thrillers, and true crime series.
</p>
</div>"""
        st.markdown(story_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_full1, col_full2 = st.columns([3, 2])
    
    with col_full1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.write("#### 📅 Release Year Trend Analysis")
        year_counts = df.groupby(['release_year', 'type']).size().reset_index(name='count')
        # Filter for years 2000 onwards for cleaner display
        year_counts = year_counts[year_counts['release_year'] >= 2000]
        fig_year = px.line(
            year_counts, 
            x='release_year', 
            y='count', 
            color='type',
            color_discrete_map={'Movie': '#e50914', 'TV Show': '#ff8a8f'}
        )
        fig_year.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f5f5f7',
            xaxis=dict(showgrid=False, title="Release Year"),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Count"),
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_year, use_container_width=True)
        story_html = """<div class="story-card">
<div class="story-header">
<svg viewBox="0 0 24 24" width="16" height="16" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line><line x1="2" y1="20" x2="2" y2="8"></line></svg>
YoY Growth & Production Trends
</div>
<p class="story-body">
Releases escalated exponentially after <strong>2015</strong>, peaking around <strong>2018–2020</strong>. This visualizes Netflix's aggressive "Originals" content spend strategy, scaling library volume rapidly to establish defensive market share against competing streaming platforms entering the industry.
</p>
</div>"""
        st.markdown(story_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_full2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.write("#### 🌍 Top 7 Content Producing Countries")
        
        # Clean country data (handles comma separated)
        df_country = df[df['country'] != 'Unknown']
        country_series = df_country['country'].str.split(', ').explode()
        country_counts = country_series.value_counts().head(7).reset_index()
        country_counts.columns = ['Country', 'Count']
        
        fig_country = px.funnel(
            country_counts,
            y='Country',
            x='Count',
            color='Country',
            color_discrete_sequence=['#e50914', '#b20710', '#7f050b', '#4c0307', '#330204', '#1f0102', '#0d0001']
        )
        fig_country.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f5f5f7',
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_country, use_container_width=True)
        story_html = """<div class="story-card">
<div class="story-header">
<svg viewBox="0 0 24 24" width="16" height="16" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
Regional Localization Insights
</div>
<p class="story-body">
While the United States remains the central content core, countries like <strong>India</strong> and the <strong>United Kingdom</strong> show massive production volumes. This supports Netflix's regional localization strategy, producing regional language originals to drive international subscription acquisition.
</p>
</div>"""
        st.markdown(story_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ------------------ ZOHO ANALYTICS INTEGRATION ------------------
    col_z1, col_z2 = st.columns([9, 2])
    with col_z1:
        st.markdown("### 📊 Zoho Business Intelligence Hub")
        st.markdown(
            "<p style='color: #8a8a93; margin-top: -10px; margin-bottom: 20px;'>Access live metrics, forecast visualizations, user sentiment, and growth trends compiled on Zoho.</p>",
            unsafe_allow_html=True
        )
    with col_z2:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("🖥️ Fullscreen", key="fs_enter", use_container_width=True):
            st.session_state.zoho_fullscreen = True
            st.rerun()
            
    st.markdown(
        """
        <div class='floating-dashboard-frame'>
            <iframe frameborder="0" width="100%" height="600" style="border: none; border-radius: 12px;" src="https://analytics.zoho.in/open-view/508314000000005131" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe>
        </div>
        """,
        unsafe_allow_html=True
    )
