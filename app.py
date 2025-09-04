import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ✅ Load API keys from secrets (safe for Streamlit Cloud)
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", "")
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")

# ✅ Load dataset
movies = pd.read_csv("Movie_Recommendations.csv")

# Preprocessing
movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
movies['overview'] = movies['overview'].fillna("")
movies['genre'] = movies['genre'].fillna("Unknown")
movies['vote_average'] = pd.to_numeric(movies['vote_average'], errors='coerce')
movies['runtime'] = pd.to_numeric(movies['runtime'], errors='coerce')

if 'date_added' not in movies.columns:
    import random
    from datetime import timedelta
    movies['date_added'] = [datetime.today() - timedelta(days=random.randint(0, 365)) for _ in range(len(movies))]

# ✅ TF-IDF vectorization
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies['overview'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# ✅ Fetch poster from OMDb
def get_poster(title):
    """Fetch movie poster (TMDB first, fallback to OMDb)."""
    # ✅ Try TMDB first
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

    # ✅ Fallback to OMDb
    if OMDB_API_KEY:
        try:
            url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
            data = requests.get(url).json()
            poster = data.get("Poster", "")
            if poster and poster != "N/A":
                return poster
        except:
            pass

    # ✅ Final fallback: placeholder
    return "https://via.placeholder.com/150"


# ✅ Get recommendations
def get_recommendations(title):
    indices = pd.Series(movies.index, index=movies['original_title'].str.lower()).drop_duplicates()
    idx = indices.get(title.lower())
    if idx is None:
        return []
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:11]  # top 10
    movie_indices = [i[0] for i in sim_scores]
    return movies.iloc[movie_indices]['original_title'].tolist()

# ✅ Fetch extra details from TMDB (streaming availability, cast, etc.)
def fetch_tmdb_details(title):
    if not TMDB_API_KEY:
        return {}
    try:
        # Search movie
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
        search_data = requests.get(search_url).json()
        if not search_data.get("results"):
            return {}
        movie_id = search_data["results"][0]["id"]

        # Movie details
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,watch/providers"
        details = requests.get(details_url).json()

        providers = details.get("watch/providers", {}).get("results", {}).get("US", {}).get("flatrate", [])
        provider_names = [p["provider_name"] for p in providers] if providers else ["Not Available"]

        cast = [c["name"] for c in details.get("credits", {}).get("cast", [])[:5]]

        return {
            "Where to Watch": provider_names,
            "Cast": cast,
            "TMDB Rating": details.get("vote_average", "N/A"),
        }
    except:
        return {}

# ✅ Local movie details
def get_movie_details(title):
    movie = movies[movies['original_title'].str.lower() == title.lower()]
    if movie.empty:
        return None
    movie = movie.iloc[0]
    details = {
        'Title': movie['original_title'],
        'Description': movie['overview'],
        'Genre': movie['genre'],
        'Rating': movie['vote_average'],
        'Runtime': movie['runtime'],
        'Release Date': movie['release_date'].strftime('%Y-%m-%d') if pd.notnull(movie['release_date']) else 'Unknown',
        'Popularity': movie['popularity'] if 'popularity' in movie else 'Unknown'
    }
    return details

# ✅ Streamlit UI
st.set_page_config(layout="wide")
st.title("🎬 Smart Movie Recommendation System")

st.sidebar.header("🔎 Filters")
genre_filter = st.sidebar.selectbox("Genre", ["All"] + sorted(movies['genre'].unique()))
min_year, max_year = st.sidebar.slider("Release Year", 1950, datetime.today().year, (2000, 2023))
min_rating = st.sidebar.slider("Minimum Rating", 0.0, 10.0, 6.0)
max_runtime = st.sidebar.slider("Maximum Runtime (min)", 60, 300, 180)

filtered = movies.copy()
if genre_filter != "All":
    filtered = filtered[filtered['genre'] == genre_filter]
filtered = filtered[
    (filtered['release_date'].dt.year >= min_year) &
    (filtered['release_date'].dt.year <= max_year) &
    (filtered['vote_average'] >= min_rating) &
    (filtered['runtime'] <= max_runtime)
]

movie_input = st.text_input("Enter a movie title:", "Inception")

if st.button("Recommend"):
    details = get_movie_details(movie_input)
    tmdb_info = fetch_tmdb_details(movie_input)

    if details is None:
        st.warning("Movie not found.")
    else:
        st.subheader(f"Details for **{movie_input}**:")
        st.image(get_poster(movie_input), width=200)

        st.markdown(f"**Description:** {details['Description']}")
        st.markdown(f"**Genre:** {details['Genre']}")
        st.markdown(f"**Rating:** {details['Rating']}")
        st.markdown(f"**Runtime:** {details['Runtime']} minutes")
        st.markdown(f"**Release Date:** {details['Release Date']}")
        st.markdown(f"**Popularity:** {details['Popularity']}")

        if tmdb_info:
            st.markdown(f"**Cast:** {', '.join(tmdb_info['Cast'])}")
            st.markdown(f"**Where to Watch:** {', '.join(tmdb_info['Where to Watch'])}")
            st.markdown(f"**TMDB Rating:** {tmdb_info['TMDB Rating']}")

        recs = get_recommendations(movie_input)
        if not recs:
            st.warning("No similar recommendations found.")
        else:
            st.subheader("Similar Movies:")
            cols = st.columns(min(len(recs), 6))
            for i, rec in enumerate(recs):
                with cols[i % 6]:
                    st.image(get_poster(rec), width=150, caption=rec)

st.subheader("🔥 Popular Now")
popular = filtered.sort_values(by='popularity', ascending=False).head(6)
cols = st.columns(6)
for i, row in enumerate(popular.itertuples()):
    with cols[i]:
        st.image(get_poster(row.original_title), width=150, caption=row.original_title)

st.subheader("🆕 Just Added")
recent = filtered.sort_values(by='date_added', ascending=False).head(6)
cols = st.columns(6)
for i, row in enumerate(recent.itertuples()):
    with cols[i]:
        st.image(get_poster(row.original_title), width=150, caption=row.original_title)

