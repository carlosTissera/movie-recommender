import pandas as pd
import ast # Para convertir strings a objetos de Python

def load_and_merge_data():
    """Carga y fusiona los datasets de películas y créditos de TMDB."""
    try: 
        movies = pd.read_csv('tmdb_5000_movies.csv')
        credits = pd.read_csv('tmdb_5000_credits.csv')
        # Fusiono los dos dataframes usando el título como clave
        data = movies.merge(credits, on='title')
        return data 
    except FileNotFoundError:
        print("Error: Asegúrate de que los archivos de TMDB están en la carpeta del proyecto.")
        exit()

# Cargar datos 
movie_data = load_and_merge_data()

# Selecciono solo las columnas a usar 
features = ['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']
movie_data = movie_data[features]

def extract_from_json_string(obj, key='name'):
    """Extrae una lista de valores de una columna con formato JSON string."""
    items = []
    for i in ast.literal_eval(obj):
        items.append(i[key].replace(" ", "")) # Unimos nombres para tratarlos como un solo tag
    return items

def get_director(obj):
    """Extrae el nombre del director del equipo."""
    for i in ast.literal_eval(obj):
        if i['job'] == 'Director':
            return [i['name'].replace(" ", "")]
    return []

# Limpiar filas con datos faltantes
movie_data.dropna(inplace=True)

# Aplicar las funciones de extracción
movie_data['genres'] = movie_data['genres'].apply(extract_from_json_string)
movie_data['keywords'] = movie_data['keywords'].apply(extract_from_json_string)
movie_data['cast'] = movie_data['cast'].apply(lambda x: extract_from_json_string(x)[:3]) # Solo los 3 actores principales
movie_data['crew'] = movie_data['crew'].apply(get_director)

# Crear la columna 'tags' combinando todo
movie_data['overview'] = movie_data['overview'].apply(lambda x: x.split())
movie_data['tags'] = movie_data['overview'] + movie_data['genres'] + movie_data['keywords'] + movie_data['cast'] + movie_data['crew']

# Crear un nuevo dataframe simplificado
clean_df = movie_data[['movie_id', 'title', 'tags']].copy()
clean_df['tags'] = clean_df['tags'].apply(lambda x: " ".join(x).lower())

#print("Preprocesamiento de datos completado.")
#print(clean_df.head())

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from thefuzz import process # <-- IMPORTANTE: Añade esta nueva importación
from sklearn.feature_extraction.text import TfidfVectorizer

# ... (El código anterior de carga y preprocesamiento de datos se mantiene igual) ...

# Vectorizar los tags
vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
vectors = vectorizer.fit_transform(clean_df['tags']).toarray()


# Calcular la matriz de similitud del coseno
similarity_matrix = cosine_similarity(vectors)
#print("Matriz de similitud calculada.")


def find_closest_title(title):
    """Encuentra el título más similar en el dataframe usando fuzzy matching."""
    # Extraemos todos los títulos de nuestro dataframe
    titles_list = clean_df['title'].tolist()
    # Usamos process.extractOne para encontrar la mejor coincidencia
    # Devuelve una tupla: (título_encontrado, score_de_similitud)
    closest_match = process.extractOne(title, titles_list)
    
    # Si la similitud es alta (ej. > 85%), aceptamos la coincidencia
    if closest_match and closest_match[1] > 85:
        return closest_match[0]
    return None

# ESTA ES LA NUEVA VERSIÓN QUE DEBES USAR EN recommender.py
def recommend(movie_title, num_recommendations=5):
    """
    Busca películas similares y DEVUELVE UNA LISTA con los títulos.
    """
    # 1. La lógica para encontrar la película y calcular las distancias es la misma
    matched_title = find_closest_title(movie_title)
    
    if not matched_title:
        # Si no encuentra la película, devuelve una lista vacía
        return []

    try:
        movie_index = clean_df[clean_df['title'] == matched_title].index[0]
    except IndexError:
        return [] # Devuelve lista vacía si hay un error

    distances = similarity_matrix[movie_index]
    # Obtenemos los índices de las películas más similares
    movies_list_indices = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:num_recommendations+1]
    
    # 2. ----> ESTA ES LA NUEVA LÓGICA <----
    # Creamos una lista vacía para guardar nuestros resultados
    recommended_movies = []
    
    # Iteramos sobre los índices de las películas recomendadas
    for i in movies_list_indices:
        # Obtenemos el título de la película usando su índice y lo añadimos a nuestra lista
        recommended_movies.append(clean_df.iloc[i[0]].title)
    
    # Finalmente, en lugar de imprimir, devolvemos la lista completa
    return recommended_movies


def get_favorite_movie_from_letterboxd(min_rating=4.0, used_movies=set()):
    """Obtiene una película de alta calificación que no se haya usado antes."""
    try:
        ratings_df = pd.read_csv('ratings.csv')
        # Filtramos por calificación y por películas no usadas
        high_rated_movies = ratings_df[(ratings_df['Rating'] >= min_rating) & (~ratings_df['Name'].isin(used_movies))]
        
        if not high_rated_movies.empty:
            favorite_movie = high_rated_movies.sample(n=1).iloc[0]
            return favorite_movie['Name']
        else:
            return None
    except FileNotFoundError:
        print("Error: No se encontró 'ratings.csv'. Colócalo en la carpeta del proyecto.")
        return None

if __name__ == "__main__":
    print("\n--- 🎬 Recomendador de Películas Personalizado ---")
    
    base_movie = get_favorite_movie_from_letterboxd()
    
    if base_movie:
        recommend(base_movie)
    else:
        # Fallback si no encuentra películas en tu historial o si ya las probó todas
        print("\nNo se encontraron películas adecuadas en tu historial. Usando un ejemplo.")
        recommend('The Dark Knight')