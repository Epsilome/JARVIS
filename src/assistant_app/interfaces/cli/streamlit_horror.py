import pandas as pd
import streamlit as st
import time
import requests

# Adjust these imports to match your folder structure
from assistant_app.services.movies import top_horror
from assistant_app.services.movies_seen import (
    is_seen_map, mark_seen, unmark_seen, all_seen
)

# --- 1. SETUP ---
st.set_page_config(page_title="Horror Night Picker", layout="wide")

st.title("🩸 Horror Night Picker")
st.caption("Personal horror movie list using TMDb + IMDb, with your own watched list.")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Filters")
    limit = st.slider("How many movies?", 5, 50, 20, step=5)
    year_from = st.number_input("From year", min_value=1960, max_value=2025, value=2000, step=1)
    min_votes = st.number_input("Min TMDb votes", min_value=10, max_value=5000, value=200, step=50)
    
    show_overview = st.checkbox("Show overview text", value=False)
    only_unwatched = st.checkbox("Hide movies I've already watched", value=False)

    # --- NEW: WATCHED LIST IN SIDEBAR ---
    st.divider()
    st.header("Watched History")
    
    watched_rows = all_seen()
    if not watched_rows:
        st.caption("No movies watched yet.")
    else:
        # usage of expander keeps the sidebar clean if the list gets long
        with st.expander(f"See all {len(watched_rows)} watched", expanded=True):
            for movie in watched_rows:
                # Simple clean list format
                st.text(f"✓ {movie.title} ({movie.year})")

# --- 3. MAIN CONTENT ---
# (Removed the "Loading movies..." text here)

# Fetch Data
seen_ids = is_seen_map()
movies = top_horror(limit=limit, year_from=year_from, min_votes=min_votes)

# Filter unwatched
if only_unwatched:
    movies = [m for m in movies if not (m.imdb_id and m.imdb_id in seen_ids)]

if not movies:
    st.info("No movies found with the current filters.")
    st.stop()

# Prepare Data
rows = []
for m in movies:
    rating = m.imdb_rating if m.imdb_rating is not None else m.tmdb_vote
    src = "IMDb" if m.imdb_rating is not None else "TMDb"
    rows.append({
        "title": m.title,
        "year": m.year,
        "rating": rating,
        "src": src,
        "tmdb_id": m.tmdb_id,
        "imdb_id": m.imdb_id or "",
        "overview": m.overview,
        "seen": (m.imdb_id in seen_ids) if m.imdb_id else False,
    })

df = pd.DataFrame(rows)

st.subheader("Top horror picks")
st.caption("Click the buttons below to mark as watched / unwatched.")

# Display Cards
for idx, row in df.iterrows():
    imdb_id = row["imdb_id"]
    tmdb_id = row["tmdb_id"]
    
    # Create columns for layout
    col1, col2 = st.columns([6, 1])

    with col1:
        watched_mark = "✓ " if row["seen"] else ""
        st.markdown(
            f"**{watched_mark}{row['title']} ({row['year']})** "
            f"— {row['rating']:.1f} {row['src']}"
        )
        
        links = []
        if imdb_id:
            links.append(f"[IMDb](https://www.imdb.com/title/{imdb_id})")
        if tmdb_id:
            links.append(f"[TMDb](https://www.themoviedb.org/movie/{tmdb_id})")
        if links:
            st.markdown(" · ".join(links))

        if show_overview and row["overview"]:
            st.caption(row["overview"])

    with col2:
        if imdb_id:
            if row["seen"]:
                # Unique key ensures buttons don't conflict
                if st.button("Unwatch", key=f"unwatch_{imdb_id}"):
                    unmark_seen(imdb_id)
                    st.rerun()
            else:
                if st.button("Mark watched ✓", key=f"watch_{imdb_id}"):
                    mark_seen(tmdb_id, imdb_id, row["title"], row["year"])
                    st.rerun()
        else:
            st.write("No IMDb id")
    
    st.divider()