import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# TMDB API key
TMDB_KEY = "6892cfa019aa8128140103ad1628e357"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Load the optimized small dataset
movies = pd.read_csv("Movie_Recommendations.csv")

# Preprocess columns
movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
movies['overview'] = movies['overview'].fillna("")
movies['genre'] = movies['genre'].fillna("Unknown")
movies['vote_average'] = pd.to_numeric(movies['vote_average'], errors='coerce')
movies['runtime'] = pd.to_numeric(movies['runtime'], errors='coerce')

# Add synthetic date_added if not available
if 'date_added' not in movies.columns:
    import random
    from datetime import timedelta
    movies['date_added'] = [datetime.today() - timedelta(days=random.randint(0, 365)) for _ in range(len(movies))]

# TF-IDF Vectorization for overview-based recommendation
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies['overview'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# OMDB API Key (replace with your own key if needed)
OMDB_API_KEY = "62e281d1"

def tmdb_api_get(endpoint, params=None):
    if params is None:
        params = {}
    params['api_key'] = TMDB_KEY
    response = requests.get(f"{TMDB_BASE_URL}/{endpoint}", params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_tmdb_poster_path(poster_path):
    if poster_path:
        return f"{TMDB_IMAGE_BASE_URL}{poster_path}"
    else:
        return "https://via.placeholder.com/150"

def get_poster(title):
    if pd.isna(title) or title.strip() == "":
        return "https://via.placeholder.com/150"
    
    try:
        url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
        data = requests.get(url).json()
        poster = data.get("Poster", "")
        if poster and poster != "N/A":
            return poster
        else:
            # fallback to TMDB poster
            search_res = tmdb_api_get("search/movie", {"query": title})
            if search_res and search_res.get("results"):
                poster_path = search_res["results"][0].get("poster_path")
                return get_tmdb_poster_path(poster_path)
            return "https://via.placeholder.com/150"
    except Exception as e:
        return "https://via.placeholder.com/150"


def get_recommendations(title):
    indices = pd.Series(movies.index, index=movies['original_title'].str.lower()).drop_duplicates()
    idx = indices.get(title.lower())
    if idx is None:
        return []
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:]
    movie_indices = [i[0] for i in sim_scores]
    return movies.iloc[movie_indices]['original_title'].tolist()

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

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🎬 Smart Movie Recommendation System")

# Input box
movie_input = st.text_input("Enter a movie title:", "Inception")

# Recommend button
if st.button("Recommend"):
    details = get_movie_details(movie_input)
    if details is None:
        st.warning("Movie not found.")
    else:
        st.subheader(f"Details for **{movie_input}**:")
        st.image(get_poster(movie_input), width=200)
        st.markdown(f"<span style='font-size:20px'><b>Description:</b> {details['Description']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Genre:</b> {details['Genre']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Rating:</b> {details['Rating']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Runtime:</b> {details['Runtime']} minutes</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Release Date:</b> {details['Release Date']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Popularity:</b> {details['Popularity']}</span>", unsafe_allow_html=True)

        recs = get_recommendations(movie_input)
        if not recs:
            st.warning("No similar recommendations found.")
        else:
            st.subheader("Similar Movies Based on Keywords:")
            cols = st.columns(min(len(recs), 6))
            for i, rec in enumerate(recs):
                with cols[i]:
                    if st.button(rec, key=f"input_rec_{rec}_{i}"):
                        st.session_state.selected_movie = rec
                        st.rerun()
                    st.image(get_poster(rec), width=150)

# Add filter button above trending section
filter_button_clicked = st.button("Filter")

# Initialize filter state
if 'show_filters' not in st.session_state:
    st.session_state.show_filters = False

if filter_button_clicked:
    st.session_state.show_filters = not st.session_state.show_filters

# Show filters popup if toggled
if st.session_state.show_filters:
    st.markdown("### Filters")
    genre_filter = st.selectbox("Genre", ["All"] + sorted(movies['genre'].unique()))
    min_year, max_year = st.slider("Release Year", 1950, datetime.today().year, (2000, 2023))
    min_rating = st.slider("Minimum Rating", 0.0, 10.0, 6.0)
    max_runtime = st.slider("Maximum Runtime (min)", 60, 300, 180)
else:
    # Default filter values if filters not shown
    genre_filter = "All"
    min_year, max_year = 1950, datetime.today().year
    min_rating = 0.0
    max_runtime = 300

# Filtered data
filtered = movies.copy()
if genre_filter != "All":
    filtered = filtered[filtered['genre'] == genre_filter]
filtered = filtered[
    (filtered['release_date'].dt.year >= min_year) &
    (filtered['release_date'].dt.year <= max_year) &
    (filtered['vote_average'] >= min_rating) &
    (filtered['runtime'] <= max_runtime)
]

# 🔥 Trending (using TMDB)
st.subheader("🔥 Trending")

trending_data = tmdb_api_get("trending/movie/week")
trending_movies = trending_data['results'][:10] if trending_data else []

cols = st.columns(min(len(trending_movies), 10))
for i, movie in enumerate(trending_movies):
    with cols[i % 10]:
        poster_url = get_tmdb_poster_path(movie.get("poster_path"))
        title = movie.get("title")
        if st.button(title, key=f"trending_{title}_{i}"):
            st.session_state.selected_movie = title
            st.rerun()
        st.image(poster_url, width=150)

# Initialize session state for selected movie
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None

# Function to display movie details and recommendations
def display_movie_details(title):
    details = get_movie_details(title)
    if details:
        st.subheader(f"Details for **{title}**:")
        st.image(get_poster(title), width=200)
        st.markdown(f"<span style='font-size:20px'><b>Description:</b> {details['Description']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Genre:</b> {details['Genre']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Rating:</b> {details['Rating']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Runtime:</b> {details['Runtime']} minutes</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Release Date:</b> {details['Release Date']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:20px'><b>Popularity:</b> {details['Popularity']}</span>", unsafe_allow_html=True)

        recs = get_recommendations(title)
        if not recs:
            st.warning("No similar recommendations found.")
        else:
            st.subheader("Similar Movies Based on Keywords:")
            cols = st.columns(min(len(recs), 6))
            for i, rec in enumerate(recs):
                with cols[i]:
                    if st.button(rec, key=f"rec_{rec}_{i}"):
                        st.session_state.selected_movie = rec
                        st.rerun()
                    st.image(get_poster(rec), width=150)

# 🆕 Just Added (from dataset)
st.subheader("🆕 Just Added")
recent = filtered.sort_values(by='date_added', ascending=False).head(6)
cols = st.columns(min(len(recent), 6))
for i, row in enumerate(recent.itertuples()):
    with cols[i]:
        title = row.original_title
        poster_url = get_poster(title)
        if st.button(title, key=f"just_added_{title}_{i}"):
            st.session_state.selected_movie = title
            st.rerun()
        st.image(poster_url, width=150)

# Genre-specific columns
genres_to_display = ['Action', 'Romance', 'Horror', 'Sci-Fi', 'Comedy']
for genre in genres_to_display:
    st.subheader(f"🎭 {genre}")
    genre_movies = movies[movies['genre'].str.contains(genre, case=False, na=False)].sort_values(by='vote_average', ascending=False).head(6)
    if not genre_movies.empty:
        genre_scroll_container = """
        <div style="display: flex; overflow-x: auto; padding: 10px 0;">
        """
        for row in genre_movies.itertuples():
            title = row.original_title
            poster_url = get_poster(title)
            genre_scroll_container += f"""
            <div style="flex: 0 0 auto; margin-right: 15px; text-align: center; cursor:pointer;" onclick="window.streamlitEvents.postMessage('{title}')">
                <img src="{poster_url}" alt="{title}" style="width:150px;"/>
                <div style="margin-top: 5px; font-weight: bold;">{title}</div>
            </div>
            """
        genre_scroll_container += "</div>"
        st.markdown(genre_scroll_container, unsafe_allow_html=True)
    else:
        st.write(f"No movies found for {genre}.")
