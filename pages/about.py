import streamlit as st

def show_about():
    # Render the new premium glassmorphism About section matching the screenshot exactly
    # We use zero leading indentation on all lines to prevent Streamlit's Markdown parser from misinterpreting them as code blocks.
    about_html = """<div class="about-container">
<h1 class="about-title">About this project</h1>
<p class="about-tagline">Advanced 3D data analytics capabilities combined with elegant glassmorphism design.</p>

<h2 class="about-subtitle">Technology stack</h2>

<div class="tech-stack-grid">
<div class="tech-card">
<div class="tech-icon-box">
<svg viewBox="0 0 24 24" width="24" height="24" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
<polyline points="16 18 22 12 16 6"></polyline>
<polyline points="8 6 2 12 8 18"></polyline>
</svg>
</div>
<div class="tech-title">React 18</div>
<div class="tech-desc">Frontend</div>
</div>

<div class="tech-card">
<div class="tech-icon-box">
<svg viewBox="0 0 24 24" width="24" height="24" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
<polyline points="16 18 22 12 16 6"></polyline>
<polyline points="8 6 2 12 8 18"></polyline>
</svg>
</div>
<div class="tech-title">Framer Motion</div>
<div class="tech-desc">Animations</div>
</div>

<div class="tech-card">
<div class="tech-icon-box">
<svg viewBox="0 0 24 24" width="24" height="24" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
<polyline points="16 18 22 12 16 6"></polyline>
<polyline points="8 6 2 12 8 18"></polyline>
</svg>
</div>
<div class="tech-title">TailwindCSS</div>
<div class="tech-desc">Styling</div>
</div>

<div class="tech-card">
<div class="tech-icon-box">
<svg viewBox="0 0 24 24" width="24" height="24" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
<polyline points="16 18 22 12 16 6"></polyline>
<polyline points="8 6 2 12 8 18"></polyline>
</svg>
</div>
<div class="tech-title">Recharts</div>
<div class="tech-desc">Data Viz</div>
</div>
</div>

<div class="arch-perf-container">
<div class="arch-perf-card">
<div class="arch-perf-header">
<div class="arch-perf-icon-box">
<svg viewBox="0 0 24 24" width="20" height="20" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
<ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
<path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path>
</svg>
</div>
<h3 class="arch-perf-title">Architecture</h3>
</div>
<p class="arch-perf-desc">
Built entirely on the client-side with React, utilizing Framer Motion for complex 3D perspective routing and state management.
</p>
</div>

<div class="arch-perf-card">
<div class="arch-perf-header">
<div class="arch-perf-icon-box">
<svg viewBox="0 0 24 24" width="20" height="20" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
</svg>
</div>
<h3 class="arch-perf-title">Performance</h3>
</div>
<p class="arch-perf-desc">
Optimized with transform-gpu, will-change, and hardware acceleration to ensure fluid 60fps 3D animations.
</p>
</div>
</div>
</div>"""
    st.markdown(about_html, unsafe_allow_html=True)
