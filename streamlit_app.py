import requests
import streamlit as st

API = "http://127.0.0.1:8000"
IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", layout="wide")

if "selected" not in st.session_state:
    st.session_state.selected = None


@st.cache_data(ttl=300, show_spinner=False)
def api_get(path, params=None):
    r = requests.get(f"{API}{path}", params=params, timeout=90)
    r.raise_for_status()
    return r.json()


def safe_get(path, params=None):
    try:
        return api_get(path, params)
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def select_movie(movie_id):
    st.session_state.selected = movie_id


def grid(cards, prefix, cols=6):
    cards = [c for c in cards if c]
    for i in range(0, len(cards), cols):
        row = st.columns(cols)
        for col, c in zip(row, cards[i : i + cols]):
            with col:
                if c.get("poster_url"):
                    st.image(c["poster_url"], use_container_width=True)
                st.caption(c["title"])
                st.button(
                    "View",
                    key=f"{prefix}_{c['tmdb_id']}",
                    on_click=select_movie,
                    args=(c["tmdb_id"],),
                )


st.title("🎬 Movie Recommender")

# ---------------- DETAILS PAGE ----------------
if st.session_state.selected:
    st.button("← Back", on_click=select_movie, args=(None,))
    d = safe_get(f"/movie/id/{st.session_state.selected}")
    if d:
        left, right = st.columns([1, 2])
        with left:
            if d.get("poster_url"):
                st.image(d["poster_url"], use_container_width=True)
        with right:
            st.header(d["title"])
            st.write(f"Release date: {d.get('release_date') or 'N/A'}")
            st.write("Genres: " + ", ".join(g["name"] for g in d.get("genres", [])))
            st.write(d.get("overview") or "No overview available.")

        with st.spinner("Finding recommendations..."):
            bundle = safe_get("/movie/search", {"query": d["title"]})

        if bundle:
            st.subheader("Similar movies (TF-IDF)")
            tf_cards = [
                x["tmdb"] for x in bundle["tfidf_recommendations"] if x.get("tmdb")
            ]
            if tf_cards:
                grid(tf_cards, "tf")
            else:
                st.info("No content-based matches found in the local dataset.")

            st.subheader("More in the same genre")
            grid(bundle["genre_recommendations"], "genre")

# ---------------- HOME / SEARCH ----------------
else:
    query = st.text_input("Search for a movie")

    if query:
        data = safe_get("/tmdb/search", {"query": query})
        results = (data or {}).get("results", [])
        cards = [
            {
                "tmdb_id": m["id"],
                "title": m.get("title", ""),
                "poster_url": f"{IMG}{m['poster_path']}" if m.get("poster_path") else None,
            }
            for m in results
            if m.get("id")
        ]
        if cards:
            grid(cards[:18], "search")
        else:
            st.warning("No movies found.")
    else:
        category = st.selectbox(
            "Browse", ["popular", "trending", "top_rated", "upcoming", "now_playing"]
        )
        cards = safe_get("/home", {"category": category, "limit": 24})
        if cards:
            grid(cards, "home")