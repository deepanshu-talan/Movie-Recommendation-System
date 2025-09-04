import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

movies = pd.read_csv("Movie_Recommendations.csv")

movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
movies['overview'] = movies['overview'].fillna("")
movies['genre'] = movies['genre'].fillna("Unknown")
movies['vote_average'] = pd.to_numeric(movies['vote_average'], errors='coerce')
movies['runtime'] = pd.to_numeric(movies['runtime'], errors='coerce')

if 'date_added' not in movies.columns:
    import random
    from datetime import timedelta
    movies['date_added'] = [datetime.today() - timedelta(days=random.randint(0, 365)) for _ in range(len(movies))]

tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies['overview'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# OMDB API Key (replace with your own key if needed)
OMDB_API_KEY = "62e281d1"

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
