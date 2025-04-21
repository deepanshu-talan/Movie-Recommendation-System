# 🎬 Movie Recommendation System

This project is an intelligent and interactive **Movie Recommendation System** built using Python. It suggests movies similar to a user-selected title by analyzing content-based features and computing similarities using **cosine similarity**. The system is powered by **Streamlit** for the frontend interface, making it easily accessible via a web browser.

---

## 🚀 Features

✨ **Content-Based Recommendations**  
Recommends movies based on metadata such as genre, keywords, and descriptions using a vector space model.

🖼️ **Movie Posters via TMDB API**  
Automatically fetches and displays movie posters by calling **The Movie Database (TMDB)** API.

⚡ **Responsive & Interactive UI**  
Built with Streamlit for a fast and reactive experience. Select a movie, and instantly get recommendations.

🔍 **Cosine Similarity Engine**  
Uses **Scikit-learn’s** `cosine_similarity` to measure similarity between movies based on feature vectors.

📦 **Clean Data Pipeline**  
Preprocessed and structured movie metadata using **Pandas** for efficient filtering and recommendations.

---

## 🛠️ Tech Stack

| Tool/Library     | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| **Python**        | Primary language used for the backend logic and data processing             |
| **Pandas**        | Data loading, preprocessing, merging, and manipulation                      |
| **Scikit-learn**  | To vectorize text features and compute cosine similarity                    |
| **Requests**      | To send HTTP requests to fetch poster data from the TMDB API                |
| **Streamlit**     | For building the frontend web app, enabling fast and easy UI deployment     |

---
Got it! Since you used the **OMDb API** instead of TMDB, I'll update the dataset and API-related parts accordingly.

Here’s the revised **Dataset** and **API Usage** section for your GitHub README:

---

## 📁 Dataset

The dataset contains metadata for **1,000 popular movies**, used to power the content-based recommendation engine. While the core dataset provides structured information like genre, runtime, and ratings, additional movie details such as posters and ratings are dynamically fetched using the **OMDb API**.

### 🔢 Columns Description

| Column             | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `id`               | Internal or TMDB-style movie ID                                             |
| `original_language`| Language the movie was originally released in                               |
| `original_title`   | Title of the movie                                                          |
| `popularity`       | Popularity score from the original data source                              |
| `release_date`     | Date when the movie was released                                            |
| `vote_average`     | Average rating based on votes                                               |
| `vote_count`       | Number of user votes                                                        |
| `genre`            | Main genre of the movie (e.g., Action, Drama)                               |
| `overview`         | A short summary of the movie’s plot                                         |
| `revenue`          | Total revenue (in USD, if available)                                        |
| `runtime`          | Duration of the movie (in minutes)                                          |
| `tagline`          | Promotional tagline (if any)                                                |

### 🧹 Notes

- Some fields contain missing values and are handled during preprocessing.
- The combined textual metadata (e.g., `overview`, `genre`, `tagline`) is used for vectorization in the recommendation model.
- Movies are recommended based on similarity in this metadata.

---

## 🌐 OMDb API Integration

This project uses the **[OMDb API](https://www.omdbapi.com/)** to enhance the user interface by fetching:

- 🎞️ **Movie Posters**  
- ⭐ **IMDb Ratings**  
- 📄 **Additional movie metadata (on demand)**

> 💡 *Make sure to get a free API key from [http://www.omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx)*

---

## 📸 Demo

Here’s a quick peek at how the app looks:

![movie_app_1](https://github.com/user-attachments/assets/1aa15cb6-0628-4950-9b5e-bec8d170fc8b)

## 🌍 Deployment

This project is deployed on **Streamlit Cloud** and is accessible at:

# 🎬 Movie Recommendation System

[![Live App](https://img.shields.io/badge/🔗%20Live%20App-Click%20Here-brightgreen?style=for-the-badge)]([https://your-streamlit-url.streamlit.app](https://movie-recommendation-system-jvmprwocvycdvytwamk5ak.streamlit.app/))

---

## ▶️ How to Run Locally

1. **Clone the Repository**

![image](https://github.com/user-attachments/assets/51078d72-9d02-4553-944e-64ca7471e487)


2. **Install Required Libraries**

![image](https://github.com/user-attachments/assets/18d4187f-1703-4b10-b84d-d715a4a85ae8)


3. **Run the Application**

![image](https://github.com/user-attachments/assets/a96a967c-cbcc-4a6a-a427-1329128669ed)

4. **Usage**

   - Choose a movie from the dropdown menu
   - The app will display the top 5 most similar movies
   - Posters and titles are shown for visual appeal

---

## 🔧 How It Works

1. **Data Preprocessing**
   - Load and clean the dataset
   - Combine features (`overview`, `genres`, `keywords`, etc.) into a single string

2. **Vectorization**
   - Use `CountVectorizer` or `TfidfVectorizer` to convert text to vectors

3. **Similarity Calculation**
   - Compute **cosine similarity** between movie vectors

4. **Recommendation Engine**
   - Sort movies by similarity score
   - Display top results with titles and posters

---

## 📌 Future Enhancements

- 🔍 Add filters: Year, IMDB Rating, Runtime
- 📡 Add collaborative filtering using user ratings
- 🧠 Use advanced NLP models (like BERT or spaCy) for better similarity
- 📱 Deploy on platforms like **Streamlit Cloud**, **Render**, or **Hugging Face Spaces**
- 💬 Add a chatbot-style interface for natural language queries
- 📊 Show metadata like popularity, release year, etc., in the UI

---

## 💡 Inspiration

This project was inspired by real-world recommendation engines used by streaming platforms like Netflix and Hulu. It’s a great foundation for learning about machine learning, APIs, and deploying interactive apps.

---
