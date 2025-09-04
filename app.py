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
            # Display recommendations as clickable tiles
            recs_scroll_container = """
            <div style="display: flex; overflow-x: auto; padding: 10px 0;">
            """
            for rec in recs:
                poster_url = get_poster(rec)
                recs_scroll_container += f"""
                <div style="flex: 0 0 auto; margin-right: 15px; text-align: center; cursor:pointer;" onclick="window.streamlitEvents.postMessage('{rec}')">
                    <img src="{poster_url}" alt="{rec}" style="width:150px;"/>
                    <div style="margin-top: 5px; font-weight: bold;">{rec}</div>
                </div>
                """
            recs_scroll_container += "</div>"
            st.markdown(recs_scroll_container, unsafe_allow_html=True)

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

# Create a horizontal scroll container using HTML and CSS
scroll_container = """
<div style="display: flex; overflow-x: auto; padding: 10px 0;">
"""

trending_data = tmdb_api_get("trending/movie/week")
trending_movies = trending_data['results'][:10] if trending_data else []

# Use streamlit-events to capture clicks on all movie tiles (trending, just added, recommendations)
movie_titles = [movie.get("title") for movie in trending_movies]

for movie in trending_movies:
    poster_url = get_tmdb_poster_path(movie.get("poster_path"))
    title = movie.get("title")
    # Each poster with title below, wrapped in a div with margin and clickable via streamlit-events
    scroll_container += f"""
    <div style="flex: 0 0 auto; margin-right: 15px; text-align: center; cursor:pointer;" onclick="window.streamlitEvents.postMessage('{title}')">
        <img src="{poster_url}" alt="{title}" style="width:150px;"/>
        <div style="margin-top: 5px; font-weight: bold;">{title}</div>
    </div>
    """

scroll_container += "</div>"

# Display the scroll container as HTML
st.markdown(scroll_container, unsafe_allow_html=True)

# Placeholder for movie details and recommendations
details_placeholder = st.empty()
recs_placeholder = st.empty()

# Listen for clicks on posters via Streamlit events (requires streamlit-events component)
try:
    from streamlit_events import streamlit_events
    events = streamlit_events(
        key="movie_tile_clicks",
        events=["message"],
        debounce_time=0,
        override_height=0,
        override_width=0,
    )
    if events and events[0] and 'message' in events[0]:
        clicked_title = events[0]['message']
        details = get_movie_details(clicked_title)
        if details:
            details_placeholder.subheader(f"Details for **{clicked_title}**:")
            details_placeholder.image(get_poster(clicked_title), width=200)
            details_placeholder.markdown(f"<span style='font-size:20px'><b>Description:</b> {details['Description']}</span>", unsafe_allow_html=True)
            details_placeholder.markdown(f"<span style='font-size:20px'><b>Genre:</b> {details['Genre']}</span>", unsafe_allow_html=True)
            details_placeholder.markdown(f"<span style='font-size:20px'><b>Rating:</b> {details['Rating']}</span>", unsafe_allow_html=True)
            details_placeholder.markdown(f"<span style='font-size:20px'><b>Runtime:</b> {details['Runtime']} minutes</span>", unsafe_allow_html=True)
            details_placeholder.markdown(f"<span style='font-size:20px'><b>Release Date:</b> {details['Release Date']}</span>", unsafe_allow_html=True)
            details_placeholder.markdown(f"<span style='font-size:20px'><b>Popularity:</b> {details['Popularity']}</span>", unsafe_allow_html=True)

            recs = get_recommendations(clicked_title)
            if not recs:
                recs_placeholder.warning("No similar recommendations found.")
            else:
                recs_placeholder.subheader("Similar Movies Based on Keywords:")
                cols = recs_placeholder.columns(min(len(recs), 6))
                for i, rec in enumerate(recs):
                    with cols[i % 6]:
                        recs_placeholder.image(get_poster(rec), width=150, caption=rec)
except ImportError:
    st.warning("streamlit-events component not installed. Click functionality on movie tiles is disabled.")

# 🆕 Just Added (from dataset)
st.subheader("🆕 Just Added")
recent = filtered.sort_values(by='date_added', ascending=False).head(6)
# Display Just Added as clickable tiles
just_added_scroll_container = """
<div style="display: flex; overflow-x: auto; padding: 10px 0;">
"""
for row in recent.itertuples():
    title = row.original_title
    poster_url = get_poster(title)
    just_added_scroll_container += f"""
    <div style="flex: 0 0 auto; margin-right: 15px; text-align: center; cursor:pointer;" onclick="window.streamlitEvents.postMessage('{title}')">
        <img src="{poster_url}" alt="{title}" style="width:150px;"/>
        <div style="margin-top: 5px; font-weight: bold;">{title}</div>
    </div>
    """
just_added_scroll_container += "</div>"
st.markdown(just_added_scroll_container, unsafe_allow_html=True)

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
