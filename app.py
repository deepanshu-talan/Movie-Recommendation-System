import streamlit as st
import requests
import os

# Load API keys from environment (set in Streamlit Cloud secrets)
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

st.set_page_config(page_title="🎬 AI-Powered Movie Recommendation System", layout="wide")
st.title("🎬 AI-Powered Movie Recommendation System")
st.write("Discover movies you'll love, powered by AI and external movie APIs.")

# ✅ Poster Fetcher (TMDB first, OMDb fallback)
def get_poster(title):
    """Fetch movie poster (TMDB first, fallback to OMDb)."""
    # TMDB
    if TMDB_API_KEY:
        try:
            url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
            data = requests.get(url).json()
            if data.get("results"):
                poster_path = data["results"][0].get("poster_path")
                if poster_path:
                    return f"https://image.tmdb.org/t/p/w500{poster_path}"
        except:
            pass

    # OMDb
    if OMDB_API_KEY:
        try:
            url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
            data = requests.get(url).json()
            poster = data.get("Poster", "")
            if poster and poster != "N/A":
                return poster
        except:
            pass

    # Placeholder
    return "https://via.placeholder.com/150?text=No+Poster"

# ✅ Search movies (from TMDB)
def search_movies(query):
    if TMDB_API_KEY:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        data = requests.get(url).json()
        return [m["title"] for m in data.get("results", []) if "title" in m]
    return []

# ✅ Recommendation system (dummy: suggest top related from TMDB)
def recommend_movies(movie_name):
    if TMDB_API_KEY:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
        data = requests.get(url).json()
        if data.get("results"):
            movie_id = data["results"][0]["id"]
            rec_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={TMDB_API_KEY}"
            rec_data = requests.get(rec_url).json()
            return [m["title"] for m in rec_data.get("results", []) if "title" in m]
    return []

# ✅ Streamlit UI
movie_name = st.text_input("🎥 Enter a movie name:", "")

if st.button("🔍 Get Recommendations"):
    if movie_name:
        st.subheader(f"Recommended Movies for **{movie_name}**:")
        recommended = recommend_movies(movie_name)
        if recommended:
            cols = st.columns(3)
            for i, rec in enumerate(recommended[:9]):  # show top 9
                with cols[i % 3]:
                    poster = get_poster(rec)
                    st.image(poster, caption=rec, use_container_width=True)
        else:
            st.warning("No recommendations found. Try another movie.")
    else:
        st.warning("Please enter a movie name to continue.")
