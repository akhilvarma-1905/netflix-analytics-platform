import streamlit as st
import pandas as pd

import re

GENRE_MAP = {
    "comedy": "Comedies", "comedies": "Comedies",
    "drama": "Dramas", "dramas": "Dramas",
    "documentar": "Documentaries",
    "horror": "Horror", "action": "Action",
    "thriller": "Thrillers",
    "romance": "Romantic", "romantic": "Romantic",
    "sci-fi": "Sci-Fi", "fiction": "Sci-Fi",
    "anime": "Anime", "kids": "Kids", "family": "Children",
}

GENRES_LIST = list(GENRE_MAP.keys())

COUNTRIES_LIST = [
    "united states", "india", "united kingdom", "canada", "japan", "france", "south korea",
    "spain", "mexico", "australia", "egypt", "turkey", "philippines", "brazil", "germany",
    "nigeria", "taiwan", "indonesia", "thailand", "italy", "colombia", "china",
]


def _cast_column(is_sqlite, is_postgres=False):
    if is_postgres:
        return 'cast_members'
    return '"cast"' if is_sqlite else "`cast`"


def _detect_genre(q):
    for g in GENRES_LIST:
        if g in q:
            return GENRE_MAP.get(g, g)
    return None


def _detect_country(q):
    for c in COUNTRIES_LIST:
        if c in q:
            return c
    return None


def _strip_query_prefix(q, prefixes):
    result = q
    for prefix in sorted(prefixes, key=len, reverse=True):
        result = result.replace(prefix, " ")
    return re.sub(r"\s+", " ", result).replace("?", "").strip()


def _extract_search_term(q):
    """Pull the subject (title, name, etc.) out of a natural-language question."""
    term = _strip_query_prefix(
        q,
        [
            "who is in the cast of", "who is the director of", "who directed",
            "tell me about", "what is the", "what is", "give me details about",
            "details about", "information about", "info on", "describe",
            "search for", "find me", "find", "show me", "list", "about",
            "cast of", "actors in", "director of", "directed by",
            "movies starring", "movies by", "films by", "films starring",
            "starring", "acted by", "recommend", "suggest", "best",
            "top", "good", "popular", "watch", "movie", "movies", "film", "films",
            "show", "shows", "tv", "some", "the", "a", "an",
        ],
    )
    return term.strip(" ,")


FALLBACK_MSG = (
    "I couldn't find an exact match in the Netflix repository. "
    "Try searching by **genre**, **actor**, **director**, or **country**."
)

EXAMPLE_QUERIES = [
    "Recommend action movies",
    "Best horror TV shows",
    "Movies directed by Christopher Nolan",
    "Shows starring Will Smith",
    "Tell me about Stranger Things",
    "How many movies are from Canada?",
]


def _no_match():
    return f"🤖 **Netflix AI Recommendation Assistant**\n\n{FALLBACK_MSG}"


def _detect_content_type(q):
    if "tv show" in q or "tv shows" in q or "series" in q:
        return "TV Show"
    if ("show" in q or "shows" in q) and "movie" not in q and "film" not in q:
        return "TV Show"
    if "movie" in q or "film" in q or "films" in q:
        return "Movie"
    return None


def _truncate(text, limit=140):
    if not text or text == "Unknown":
        return "N/A"
    text = str(text).strip()
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _top_genres_from_db(cursor):
    from collections import Counter
    cursor.execute("SELECT listed_in FROM netflix WHERE listed_in IS NOT NULL")
    genres = Counter()
    for (listed_in,) in cursor.fetchall():
        for g in str(listed_in).split(","):
            g = g.strip()
            if g:
                genres[g] += 1
    return genres.most_common(5)


def generate_neural_response(db_conn, question):
    """Netflix-only mini AI assistant — recommendations, search, and catalog analytics."""
    q = question.lower().strip()
    if not q:
        return ""

    if db_conn is None:
        return (
            "🤖 **Netflix AI Recommendation Assistant**\n\n"
            "Catalog database is offline. Please reload the app and try again."
        )

    try:
        # Determine placeholder style and random function
        import sqlite3
        is_sqlite = isinstance(db_conn, sqlite3.Connection)
        placeholder = '?' if is_sqlite else '%s'
        
        # Check if connection is PostgreSQL
        is_postgres = False
        if not is_sqlite:
            db_module = type(db_conn).__module__
            if "psycopg2" in db_module or "postgresql" in db_module:
                is_postgres = True
                
        rand_func = "RANDOM()" if (is_sqlite or is_postgres) else "RAND()"
        
        cursor = db_conn.cursor()
        cast_col = _cast_column(is_sqlite, is_postgres)
        content_type = _detect_content_type(q)
        detected_country = _detect_country(q)
        detected_genre = _detect_genre(q)

        # Greetings
        if q in ["hi", "hello", "hey", "greetings", "yo", "sup", "howdy"]:
            examples = "\n".join(f"• *{e}*" for e in EXAMPLE_QUERIES)
            return (
                "👋 **Netflix AI Recommendation Assistant**\n\n"
                "I help you explore the Netflix catalog — recommendations, cast, directors, "
                "countries, and analytics. **Netflix queries only.**\n\n"
                f"**Try asking:**\n{examples}"
            )

        if any(x in q for x in ["who are you", "what is your name", "what do you do", "help", "instructions"]):
            return (
                "🤖 **Netflix AI Recommendation Assistant**\n\n"
                "Smart engine for **recommendations**, **genre search**, **cast/director lookup**, "
                "**country filters**, **release years**, and **catalog stats**.\n\n"
                "Examples: *Recommend action movies* · *Shows starring Will Smith* · "
                "*How many movies are from Canada?*"
            )

        off_topic_words = [
            "weather", "recipe", "bitcoin", "stock price", "football score",
            "write an essay", "homework help", "python tutorial", "javascript code",
        ]
        if any(w in q for w in off_topic_words):
            return (
                "🤖 **Netflix AI Recommendation Assistant**\n\n"
                "I only answer **Netflix catalog** questions — not general chat.\n\n"
                f"{FALLBACK_MSG}"
            )

        # Analytics: popular genres / insights
        if any(
            x in q
            for x in [
                "most popular genre", "popular genre", "dominant genre",
                "popular genres", "genre insight", "analytics insight",
                "catalog insight", "netflix insight",
            ]
        ):
            top = _top_genres_from_db(cursor)
            if top:
                leader, count = top[0]
                lines = "\n".join(f"{i}. **{g}** — {c:,} titles" for i, (g, c) in enumerate(top, 1))
                return (
                    f"📊 **Netflix Insight**\n\n"
                    f"**{leader}** is the most dominant genre ({count:,} titles).\n\n"
                    f"**Top genres:**\n{lines}"
                )

        # Trending TV shows
        if "trending" in q and (content_type == "TV Show" or "tv" in q or "show" in q or content_type is None):
            cursor.execute(
                f"SELECT title, release_year, rating FROM netflix WHERE type = 'TV Show' "
                f"ORDER BY year_added DESC, release_year DESC LIMIT 5"
            )
            rows = cursor.fetchall()
            if rows:
                lines = "\n".join(f"{i}. **{r[0]}** ({r[1]} · {r[2]})" for i, r in enumerate(rows, 1))
                return f"📺 **Trending TV Shows**\n\n{lines}"

        # Catalog counts
        if any(x in q for x in ["how many", "count of", "number of", "total"]):
            sql = "SELECT COUNT(*) FROM netflix WHERE 1=1"
            params = []
            label_parts = []

            if content_type == "Movie":
                sql += " AND type = 'Movie'"
                label_parts.append("movies")
            elif content_type == "TV Show":
                sql += " AND type = 'TV Show'"
                label_parts.append("TV shows")
            else:
                label_parts.append("titles")

            if detected_country:
                sql += f" AND country LIKE {placeholder}"
                params.append(f"%{detected_country}%")
                label_parts.append(f"from {detected_country.title()}")

            if detected_genre:
                sql += f" AND listed_in LIKE {placeholder}"
                params.append(f"%{detected_genre}%")
                label_parts.append(detected_genre.lower())

            cursor.execute(sql, tuple(params))
            count = cursor.fetchone()[0]
            label = " ".join(label_parts)
            return (
                f"📊 **Netflix Catalog Stat**\n\n"
                f"There are **{count:,}** {label} in the repository."
            )

        # Top content from country
        if detected_country and any(x in q for x in ["top", "content", "from", "netflix"]):
            limit = 5
            m = re.search(r"top\s+(\d+)", q)
            if m:
                limit = min(int(m.group(1)), 10)
            cursor.execute(
                f"SELECT title, type, release_year, rating FROM netflix "
                f"WHERE country LIKE {placeholder} ORDER BY release_year DESC LIMIT {limit}",
                (f"%{detected_country}%",),
            )
            rows = cursor.fetchall()
            if rows:
                country_label = detected_country.title()
                lines = "\n".join(f"{i}. **{r[0]}** ({r[2]} · {r[1]})" for i, r in enumerate(rows, 1))
                return f"🌍 **Top Netflix Content from {country_label}**\n\n{lines}"

        # Director search
        if any(x in q for x in ["directed by", "movies by", "films by", "director of", "who directed"]):
            if "director of" in q or "who directed" in q:
                title_search = _strip_query_prefix(q, ["who is the director of", "who directed", "director of"])
                cursor.execute(
                    f"SELECT title, director, release_year, type FROM netflix "
                    f"WHERE title LIKE {placeholder} ORDER BY LENGTH(title) ASC LIMIT 1",
                    (f"%{title_search}%",),
                )
                row = cursor.fetchone()
                if row:
                    director = row[1] if row[1] != "Unknown" else "Unknown"
                    return (
                        f"🎬 **Director Lookup**\n\n"
                        f"**{row[0]}** ({row[2]}) → directed by **{director}**"
                    )

            name_search = _extract_search_term(q)
            if name_search and len(name_search) > 2:
                cursor.execute(
                    f"SELECT title, release_year, type FROM netflix "
                    f"WHERE director LIKE {placeholder} ORDER BY release_year DESC LIMIT 5",
                    (f"%{name_search}%",),
                )
                rows = cursor.fetchall()
                if rows:
                    lines = "\n".join(f"{i}. **{r[0]}** ({r[1]})" for i, r in enumerate(rows, 1))
                    return (
                        f"🎬 **Movies by {name_search.title()}**\n\n{lines}"
                    )

        # Cast / actor search
        if any(x in q for x in ["cast of", "actors in", "starring", "starred in", "acted by", "featuring"]):
            if "cast of" in q or "actors in" in q:
                title_search = _strip_query_prefix(q, ["who is in the cast of", "cast of", "actors in"])
                cursor.execute(
                    f"SELECT title, {cast_col}, release_year FROM netflix "
                    f"WHERE title LIKE {placeholder} ORDER BY LENGTH(title) ASC LIMIT 1",
                    (f"%{title_search}%",),
                )
                row = cursor.fetchone()
                if row:
                    cast_txt = _truncate(row[1], 200)
                    return f"👥 **Cast of {row[0]}** ({row[2]})\n\n{cast_txt}"

            actor_search = _extract_search_term(q)
            if actor_search and len(actor_search) > 2:
                cursor.execute(
                    f"SELECT title, release_year, type FROM netflix "
                    f"WHERE {cast_col} LIKE {placeholder} ORDER BY release_year DESC LIMIT 5",
                    (f"%{actor_search}%",),
                )
                rows = cursor.fetchall()
                if rows:
                    lines = "\n".join(f"• **{r[0]}** ({r[1]})" for r in rows)
                    return (
                        f"🎭 **Titles starring {actor_search.title()}**\n\n{lines}"
                    )

        # Recommendations / best picks
        if any(
            x in q
            for x in [
                "recommend", "suggest", "best", "good", "what to watch",
                "to watch", "pick", "suggestion", "show me",
            ]
        ):
            genre_label = detected_genre or "Dramas"
            limit = 3
            m = re.search(r"top\s+(\d+)", q)
            if m:
                limit = min(int(m.group(1)), 10)

            sql = (
                f"SELECT title, type, release_year, rating FROM netflix "
                f"WHERE listed_in LIKE {placeholder}"
            )
            params = [f"%{genre_label}%"]

            if content_type:
                sql += f" AND type = {placeholder}"
                params.append(content_type)

            sql += f" ORDER BY {rand_func} LIMIT {limit}"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            if rows:
                type_label = content_type or "Titles"
                if content_type == "Movie":
                    type_label = "Movies"
                elif content_type == "TV Show":
                    type_label = "TV Shows"
                heading = f"🎬 **Recommended {genre_label} {type_label}**"
                if "horror" in q and content_type == "TV Show":
                    heading = "📺 **Best Horror TV Shows**"
                elif "action" in q and content_type == "Movie":
                    heading = "🎬 **Recommended Action Movies**"
                elif "comedy" in q and content_type == "Movie":
                    heading = "😂 **Top Comedy Movies**"
                lines = "\n".join(f"{i}. **{r[0]}** ({r[2]})" for i, r in enumerate(rows, 1))
                return f"{heading}\n\n{lines}"

        # Top N lists
        top_match = re.search(r"top\s+(\d+)", q)
        if top_match:
            limit = min(max(int(top_match.group(1)), 1), 10)
            sql = f"SELECT title, type, release_year, rating FROM netflix WHERE 1=1"
            params = []
            if content_type:
                sql += f" AND type = {placeholder}"
                params.append(content_type)
            if detected_genre:
                sql += f" AND listed_in LIKE {placeholder}"
                params.append(f"%{detected_genre}%")
            if detected_country:
                sql += f" AND country LIKE {placeholder}"
                params.append(f"%{detected_country}%")
            sql += f" ORDER BY release_year DESC LIMIT {limit}"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            if rows:
                lines = "\n".join(f"{i}. **{r[0]}** ({r[2]} · {r[1]})" for i, r in enumerate(rows, 1))
                return f"📋 **Top {len(rows)} Picks**\n\n{lines}"

        # Release year lookup
        if any(x in q for x in ["release year", "released in", "when was", "when did"]):
            title_search = _extract_search_term(q)
            if title_search:
                cursor.execute(
                    f"SELECT title, release_year, type FROM netflix "
                    f"WHERE title LIKE {placeholder} ORDER BY LENGTH(title) ASC LIMIT 1",
                    (f"%{title_search}%",),
                )
                row = cursor.fetchone()
                if row:
                    return (
                        f"📅 **Release Year**\n\n"
                        f"**{row[0]}** ({row[2]}) was released in **{row[1]}**."
                    )

        # Title details: tell me about / about
        if any(x in q for x in ["tell me about", "about", "what is", "describe", "info on"]):
            title_search = _extract_search_term(q)
            if title_search:
                cursor.execute(
                    f"SELECT title, type, release_year, director, {cast_col}, country, "
                    f"listed_in, description, rating FROM netflix "
                    f"WHERE title LIKE {placeholder} ORDER BY LENGTH(title) ASC LIMIT 1",
                    (f"%{title_search}%",),
                )
                row = cursor.fetchone()
                if row:
                    icon = "📺" if row[1] == "TV Show" else "🎬"
                    return (
                        f"{icon} **{row[0]}**\n\n"
                        f"**Type:** {row[1]} · **Year:** {row[2]} · **Rating:** {row[8]}\n"
                        f"**Genres:** {_truncate(row[6], 80)}\n"
                        f"**Director:** {row[3]} · **Country:** {row[5]}\n"
                        f"**Cast:** {_truncate(row[4], 100)}\n\n"
                        f"_{_truncate(row[7], 160)}_"
                    )

        # Genre-only browse
        if detected_genre and not detected_country:
            cursor.execute(
                f"SELECT title, type, release_year FROM netflix "
                f"WHERE listed_in LIKE {placeholder} ORDER BY release_year DESC LIMIT 5",
                (f"%{detected_genre}%",),
            )
            rows = cursor.fetchall()
            if rows:
                lines = "\n".join(f"{i}. **{r[0]}** ({r[2]} · {r[1]})" for i, r in enumerate(rows, 1))
                return f"🎯 **{detected_genre} on Netflix**\n\n{lines}"

        # Title fallback — supports queries like "Stranger Things" without keywords
        for term in dict.fromkeys([question.strip(), _extract_search_term(q)]):
            if len(term) < 2:
                continue
            cursor.execute(
                f"SELECT title, type, release_year, director, {cast_col}, country, "
                f"listed_in, description, rating FROM netflix "
                f"WHERE title LIKE {placeholder} ORDER BY LENGTH(title) ASC LIMIT 1",
                (f"%{term}%",),
            )
            row = cursor.fetchone()
            if row:
                icon = "📺" if row[1] == "TV Show" else "🎬"
                return (
                    f"{icon} **{row[0]}**\n\n"
                    f"**Type:** {row[1]} · **Year:** {row[2]} · **Rating:** {row[8]}\n"
                    f"**Genres:** {_truncate(row[6], 80)}\n"
                    f"**Director:** {row[3]} · **Country:** {row[5]}\n"
                    f"**Cast:** {_truncate(row[4], 100)}\n\n"
                    f"_{_truncate(row[7], 160)}_"
                )

        return _no_match()

    except Exception as e:
        return f"🤖 **Assistant Error**\n\nCould not process that query: {str(e)}"


def _init_ai_state():
    """Single source of truth for assistant UI state."""
    defaults = {"asked": "", "answer": "", "time": "", "input_id": 0}
    if "ai_state" not in st.session_state:
        st.session_state.ai_state = defaults.copy()
    for key, val in defaults.items():
        if key not in st.session_state.ai_state:
            st.session_state.ai_state[key] = val
    # Drop legacy keys that break Clear (widget cache)
    for legacy in ("neural_query", "neural_response", "neural_query_input", "neural_query_time"):
        st.session_state.pop(legacy, None)


def _clear_ai_chat():
    """Reset assistant — bump input_id and remove cached text-input widget state."""
    prev_id = st.session_state.ai_state.get("input_id", 0)
    st.session_state.ai_state = {"asked": "", "answer": "", "time": "", "input_id": prev_id + 1}
    st.session_state.pop(f"ai_query_{prev_id}", None)


def _submit_ai_query(db_conn, query_text):
    import datetime
    text = (query_text or "").strip()
    if not text:
        st.session_state.ai_state["answer"] = (
            "🤖 **Netflix AI Recommendation Assistant**\n\n"
            "Type a question above, or tap a **quick example**."
        )
        st.session_state.ai_state["asked"] = ""
        st.session_state.ai_state["time"] = ""
        return
    st.session_state.ai_state["asked"] = text
    st.session_state.ai_state["answer"] = generate_neural_response(db_conn, text)
    st.session_state.ai_state["time"] = datetime.datetime.now().strftime("%I:%M %p")


def _render_query_assistant(db_conn):
    """AI query tab — search box, quick examples, and answer panel."""
    _init_ai_state()
    state = st.session_state.ai_state
    input_key = f"ai_query_{state['input_id']}"

    st.markdown('<div class="ai-assistant-wrap">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ai-assistant-panel">
            <div class="ai-assistant-header">
                <div class="ai-assistant-icon">
                    <svg viewBox="0 0 24 24" width="22" height="22" stroke="#fff" stroke-width="2" fill="none">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                </div>
                <div>
                    <h3 class="ai-assistant-title">AI Recommendation Assistant</h3>
                    <p class="ai-assistant-subtitle">Netflix catalog · smart recommendations · live analytics</p>
                </div>
                <span class="ai-assistant-badge">ONLINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="ai-examples-label">Quick examples — tap to ask</p>'
        '<div class="ai-examples-anchor"></div>',
        unsafe_allow_html=True,
    )
    ex_cols = st.columns(3)
    for i, example in enumerate(EXAMPLE_QUERIES):
        with ex_cols[i % 3]:
            st.button(
                example,
                key=f"ai_example_{i}_{state['input_id']}",
                use_container_width=True,
                on_click=_submit_ai_query,
                args=(db_conn, example),
            )

    st.markdown('<div class="ai-query-section"><div class="neural-query-anchor"></div>', unsafe_allow_html=True)

    with st.form("neural_query_form", clear_on_submit=False):
        col_inp, col_btn = st.columns([8.5, 1.5])
        with col_inp:
            query_val = st.text_input(
                "AI Assistant Query",
                placeholder="Ask anything… e.g. Recommend action movies",
                label_visibility="collapsed",
                key=input_key,
            )
        with col_btn:
            submit_clicked = st.form_submit_button("Ask ✦", use_container_width=True, type="primary")

    if submit_clicked:
        with st.spinner("Analyzing Netflix catalog…"):
            _submit_ai_query(db_conn, query_val)

    st.markdown("</div>", unsafe_allow_html=True)

    act_col1, act_col2, _ = st.columns([1.2, 1.2, 6])
    with act_col1:
        st.button("Clear", key=f"ai_clear_{state['input_id']}", use_container_width=True, on_click=_clear_ai_chat)
    with act_col2:
        if state["answer"] and state["asked"]:
            st.button(
                "Re-run",
                key=f"ai_rerun_{state['input_id']}",
                use_container_width=True,
                on_click=_submit_ai_query,
                args=(db_conn, state["asked"]),
            )

    # Answer column — single panel
    st.markdown('<div class="ai-answer-anchor"></div>', unsafe_allow_html=True)
    if state["answer"]:
        with st.container(border=True):
            head_l, head_r = st.columns([4, 1])
            with head_l:
                st.markdown("##### 🤖 Assistant")
            with head_r:
                if state["time"]:
                    st.caption(state["time"])
            if state["asked"]:
                st.markdown(f"**You asked:** {state['asked']}")
            st.markdown(state["answer"])
    else:
        st.markdown(
            """
            <div class="ai-empty-state">
                <div class="ai-empty-icon">🎬</div>
                <p class="ai-empty-title">Ready to explore the Netflix catalog</p>
                <p class="ai-empty-desc">Ask about genres, actors, directors, countries, or any title.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _apply_dashboard_filters(df, genre, content_type, country, rating):
    f_df = df.copy()
    if genre != "All Genres":
        f_df = f_df[f_df["listed_in"].str.contains(genre, na=False, case=False)]
    if content_type != "All Types":
        f_df = f_df[f_df["type"] == content_type]
    if country != "All Countries":
        f_df = f_df[f_df["country"].str.contains(country, na=False, case=False)]
    if rating != "All Ratings":
        f_df = f_df[f_df["rating"] == rating]
    return f_df


def _compute_dashboard_metrics(f_df):
    from collections import Counter

    empty = {
        "count": 0, "pop_genre": "N/A", "pop_country": "N/A", "pop_year": "N/A",
        "pop_rating": "N/A", "m_pct": 0, "tv_pct": 0, "m_count": 0, "tv_count": 0,
        "avg_year": "N/A", "year_range": "N/A", "rec_rows": [], "genre_pills": [],
    }
    if f_df.empty:
        return empty

    f_genres, f_countries = [], []
    for g in f_df["listed_in"].dropna():
        f_genres.extend([x.strip() for x in str(g).split(",") if x.strip()])
    for c in f_df["country"].dropna():
        f_countries.extend([x.strip() for x in str(c).split(",") if x.strip() and x.strip() != "Unknown"])

    type_counts = f_df["type"].value_counts()
    tot = len(f_df)
    m_count = int(type_counts.get("Movie", 0))
    tv_count = int(type_counts.get("TV Show", 0))
    m_pct = int(round((m_count / tot) * 100)) if tot else 0
    tv_pct = 100 - m_pct

    non_empty_years = f_df["release_year"].dropna()
    pop_year = int(f_df["release_year"].mode()[0]) if not non_empty_years.empty else "N/A"
    avg_year = int(round(f_df["release_year"].mean())) if not non_empty_years.empty else "N/A"

    pop_rating = f_df["rating"].mode()[0] if not f_df["rating"].dropna().empty else "N/A"
    if pop_rating in ("Unknown", ""):
        pop_rating = "N/A"

    rec_rows = (
        f_df.sort_values(by="release_year", ascending=False)[["title", "type", "release_year", "rating"]]
        .head(5)
        .to_dict("records")
    )
    genre_pills = [g for g, _ in Counter(f_genres).most_common(4)]

    return {
        "count": tot,
        "pop_genre": Counter(f_genres).most_common(1)[0][0] if f_genres else "N/A",
        "pop_country": Counter(f_countries).most_common(1)[0][0] if f_countries else "N/A",
        "pop_year": pop_year,
        "pop_rating": pop_rating,
        "m_pct": m_pct,
        "tv_pct": tv_pct,
        "m_count": m_count,
        "tv_count": tv_count,
        "avg_year": avg_year,
        "year_range": f"{int(f_df['release_year'].min())} – {int(f_df['release_year'].max())}",
        "rec_rows": rec_rows,
        "genre_pills": genre_pills,
    }


def _reset_dashboard_filters():
    st.session_state.dash_genre = "All Genres"
    st.session_state.dash_type = "All Types"
    st.session_state.dash_country = "All Countries"
    st.session_state.dash_rating = "All Ratings"


def _render_live_dashboard(df):
    """Real-Time Dashboard & Recommendation Insights — interactive filters and KPIs."""
    from collections import Counter

    st.markdown('<div class="live-dash-anchor"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sync-container dash-v2">
            <div class="sync-header">
                <div class="sync-title-area">
                    <h2 class="sync-main-title">Real-Time Dashboard & Recommendation Insights</h2>
                    <p class="sync-subtitle">Filters update every metric and recommendation instantly — no page reload needed.</p>
                </div>
                <div class="sync-badge"><span class="sync-pulse"></span>Live Sync</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    all_genres = []
    for g_list in df["listed_in"].dropna():
        all_genres.extend([g.strip() for g in str(g_list).split(",")])
    top_genres = ["All Genres"] + [g for g, _ in Counter(all_genres).most_common(15)]

    all_countries = []
    for c_list in df["country"].dropna():
        all_countries.extend([c.strip() for c in str(c_list).split(",") if c.strip() != "Unknown"])
    top_countries = ["All Countries"] + [c for c, _ in Counter(all_countries).most_common(15)]

    top_ratings = ["All Ratings"] + [
        r for r in df["rating"].value_counts().index if r not in ("Unknown", "")
    ]

    st.markdown('<div class="dash-filter-panel"><p class="dash-filter-label">Refine catalog view</p></div>', unsafe_allow_html=True)

    pf1, pf2, pf3, pf4, pf5 = st.columns([1, 1, 1, 1, 0.7])
    horror_genre = next((g for g in top_genres if "horror" in g.lower()), "All Genres")
    with pf1:
        if st.button("🎬 Movies", key="dash_pre_movies", use_container_width=True):
            _reset_dashboard_filters()
            st.session_state.dash_type = "Movie"
            st.rerun()
    with pf2:
        if st.button("📺 TV Shows", key="dash_pre_tv", use_container_width=True):
            _reset_dashboard_filters()
            st.session_state.dash_type = "TV Show"
            st.rerun()
    with pf3:
        if st.button("🇮🇳 India", key="dash_pre_india", use_container_width=True):
            _reset_dashboard_filters()
            st.session_state.dash_country = "India"
            st.rerun()
    with pf4:
        if st.button("👻 Horror", key="dash_pre_horror", use_container_width=True):
            _reset_dashboard_filters()
            st.session_state.dash_genre = horror_genre
            st.rerun()
    with pf5:
        if st.button("↺ Reset", key="dash_reset", use_container_width=True, on_click=_reset_dashboard_filters):
            pass

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        selected_genre = st.selectbox("Genre", top_genres, key="dash_genre")
    with fc2:
        selected_type = st.selectbox("Type", ["All Types", "Movie", "TV Show"], key="dash_type")
    with fc3:
        selected_country = st.selectbox("Country", top_countries, key="dash_country")
    with fc4:
        selected_rating = st.selectbox("Rating", top_ratings, key="dash_rating")

    f_df = _apply_dashboard_filters(df, selected_genre, selected_type, selected_country, selected_rating)
    total = len(df)
    match_count = len(f_df)
    pct_catalog = round((match_count / total) * 100, 1) if total else 0

    active_filters = []
    if selected_genre != "All Genres":
        active_filters.append(selected_genre)
    if selected_type != "All Types":
        active_filters.append(selected_type)
    if selected_country != "All Countries":
        active_filters.append(selected_country)
    if selected_rating != "All Ratings":
        active_filters.append(selected_rating)

    chips_html = "".join(f'<span class="dash-chip">{c}</span>' for c in active_filters) or '<span class="dash-chip dash-chip-muted">No filters — full catalog</span>'
    st.markdown(
        f"""
        <div class="dash-result-bar">
            <span class="dash-result-count"><strong>{match_count:,}</strong> titles</span>
            <span class="dash-result-pct">{pct_catalog}% of catalog ({total:,} total)</span>
            <div class="dash-chips">{chips_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if f_df.empty:
        st.markdown(
            """
            <div class="dash-empty-state">
                <p class="dash-empty-title">No titles match these filters</p>
                <p class="dash-empty-desc">Try removing a filter or use a quick preset above.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    m = _compute_dashboard_metrics(f_df)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Matching titles", f"{m['count']:,}", f"{pct_catalog}% of library")
    k2.metric("Top genre", m["pop_genre"][:18] + ("…" if len(str(m["pop_genre"])) > 18 else ""))
    k3.metric("Top country", m["pop_country"][:18] + ("…" if len(str(m["pop_country"])) > 18 else ""))
    k4.metric("Avg release year", m["avg_year"])

    st.markdown('<p class="dash-split-label">Movies vs TV Shows split</p>', unsafe_allow_html=True)
    split_l, split_r = st.columns([1, 1])
    with split_l:
        st.progress(m["m_pct"] / 100, text=f"Movies {m['m_pct']}% ({m['m_count']:,})")
    with split_r:
        st.progress(m["tv_pct"] / 100, text=f"TV Shows {m['tv_pct']}% ({m['tv_count']:,})")

    st.markdown(
        """
        <div class="dashboard-insights-header">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="#e50914" stroke-width="2.5" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/>
                <line x1="15" y1="3" x2="15" y2="21"/><line x1="3" y1="9" x2="21" y2="9"/>
            </svg>
            Dashboard Insights
        </div>
        """,
        unsafe_allow_html=True,
    )

    insight_cards = [
        ("Most Popular Genre", m["pop_genre"], "Highest density in your filtered view.", True),
        ("Top Country", m["pop_country"], "Leading production region.", False),
        ("Peak Release Year", m["pop_year"], "Most common release year in selection.", True),
        ("Top Rating", m["pop_rating"], "Dominant maturity classification.", True),
        ("Year Span", m["year_range"], "Earliest to latest release in filter.", False),
        ("Avg Release Year", m["avg_year"], "Mean release year for matched titles.", False),
    ]
    rows = [insight_cards[i : i + 3] for i in range(0, 6, 3)]
    cards_html = '<div class="dashboard-grid-3x2">'
    for row in rows:
        for title, val, desc, highlight in row:
            hl = " highlight-red" if highlight else ""
            cards_html += f"""
            <div class="futuristic-card">
                <div class="card-top"><p class="card-title-text">{title}</p></div>
                <h3 class="card-val{hl}">{val}</h3>
                <p class="card-desc-text">{desc}</p>
            </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    rec_list = ""
    for i, row in enumerate(m["rec_rows"], 1):
        badge = "📺" if row["type"] == "TV Show" else "🎬"
        rec_list += (
            f'<li class="rec-title-item">'
            f'<span class="rec-rank">{i}</span>'
            f'<span class="rec-badge">{badge}</span>'
            f'<span class="rec-name">{row["title"]}</span>'
            f'<span class="rec-meta">{row["release_year"]} · {row["rating"]}</span>'
            f"</li>"
        )
    pills = "".join(f'<span class="genre-pill">{g}</span>' for g in m["genre_pills"])

    st.markdown(
        f"""
        <div class="dashboard-insights-header rec-header">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="#e50914" stroke-width="2.5" fill="none">
                <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Recommendation Insights
        </div>
        <div class="dashboard-grid-rec">
            <div class="futuristic-card rec-card-wide">
                <p class="card-title-text">Top picks for your filters</p>
                <ul class="rec-title-list">{rec_list}</ul>
                <p class="card-desc-text">Newest releases matching your current selection.</p>
            </div>
            <div class="futuristic-card">
                <p class="card-title-text">Genre mix</p>
                <div class="genre-pill-row">{pills or '<span class="genre-pill">—</span>'}</div>
                <p class="card-desc-text">Top categories in this view.</p>
            </div>
            <div class="futuristic-card">
                <p class="card-title-text">Content split</p>
                <h3 class="card-val">{m['m_count']:,} <span class="card-val-sm">Movies</span></h3>
                <h3 class="card-val">{m['tv_count']:,} <span class="card-val-sm">TV Shows</span></h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)


def show_insights(df, db_conn):
    st.markdown("<h1 class='glowing-title neon-text-red' style='text-align: center; margin-bottom: 20px;'>BUSINESS INSIGHTS & INTEL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8a8a93; margin-bottom: 40px;'>Strategic conclusions, platform growth trends, and real-time database query inspections.</p>", unsafe_allow_html=True)

    _render_live_dashboard(df)

    # ------------------ TOP 10 INSIGHT STORY CARDS ------------------
    insights_data = [
        {
            "num": 1,
            "title": "Exponential Growth",
            "stat": "287% Increase",
            "desc": "Since 2015, Netflix has massively scaled original production to compete globally.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>"""
        },
        {
            "num": 2,
            "title": "Drama Dominates",
            "stat": "33.6% Share",
            "desc": "Drama remains the most produced genre, appealing to broad international audiences.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg>"""
        },
        {
            "num": 3,
            "title": "Movies vs Series",
            "stat": "69% Movies",
            "desc": "Despite popular belief, movies vastly outnumber TV shows in the total library.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>"""
        },
        {
            "num": 4,
            "title": "Global Footprint",
            "stat": "147 Countries",
            "desc": "Content sources span globally, with the US, India, and UK leading production.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>"""
        },
        {
            "num": 5,
            "title": "Mature Focus",
            "stat": "TV-MA Leader",
            "desc": "The largest chunk of content is rated TV-MA, indicating a strong focus on adult demographics.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>"""
        },
        {
            "num": 6,
            "title": "Quality Shift",
            "stat": "7.2 Avg Rating",
            "desc": "Recent strategic pivots show a focus on higher quality rather than pure quantity.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>"""
        },
        {
            "num": 7,
            "title": "The Golden Year",
            "stat": "2019 Peak",
            "desc": "2019 saw the highest number of release additions before pandemic disruptions.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>"""
        },
        {
            "num": 8,
            "title": "International Diversity",
            "stat": "K-Drama Rise",
            "desc": "South Korean and non-English content has seen a massive surge in global popularity.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>"""
        },
        {
            "num": 9,
            "title": "Documentary Surge",
            "stat": "Top 5 Genre",
            "desc": "True crime and nature documentaries have cemented a permanent high-engagement niche.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>"""
        },
        {
            "num": 10,
            "title": "Standup Comedy",
            "stat": "Niche Power",
            "desc": "Exclusive standup specials have a highly loyal user base and low production costs.",
            "icon": """<svg viewBox="0 0 24 24" width="18" height="18" stroke="#e50914" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v1a7 7 0 0 1-14 0v-1"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>"""
        }
    ]

    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 25px;">
        <svg viewBox="0 0 24 24" width="28" height="28" stroke="#e50914" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px; filter: drop-shadow(0 0 6px rgba(229, 9, 20, 0.6));">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
        <h2 style="margin: 0; font-family: 'Orbitron', sans-serif; font-size: 26px; color: #ffffff; text-shadow: 0 0 10px rgba(255,255,255,0.15);">Top 10 Insights</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Insight cards — 2-column grid (mobile-friendly)
    for row_start in range(0, len(insights_data), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = row_start + j
            if idx >= len(insights_data):
                break
            item = insights_data[idx]
            card_html = f"""
            <div class="insight-card">
                <div class="insight-watermark">{item['num']}</div>
                <div class="insight-icon-box">{item['icon']}</div>
                <div class="insight-title">{item['title']}</div>
                <div class="insight-stat">{item['stat']}</div>
                <div class="insight-desc">{item['desc']}</div>
            </div>
            """
            with col:
                st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)


def show_ai_assistant_page(df, db_conn):
    st.markdown("<h1 class='glowing-title neon-text-red' style='text-align: center; margin-bottom: 20px;'>AI RECOMMENDATION ASSISTANT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8a8a93; margin-bottom: 40px;'>Conversational Netflix intelligence — ask about catalog data, trends, and content metrics.</p>", unsafe_allow_html=True)
    _render_query_assistant(db_conn)

