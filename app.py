# app.py - Versión Final para Despliegue en Cuentas Gratuitas

from flask import Flask, render_template, request
import requests
import config # Importamos nuestro nuevo archivo de configuración

# --- CONFIGURACIÓN INICIAL ---
app = Flask(__name__)

# La clave de API se lee ahora desde el archivo config.py
API_KEY = config.API_KEY 

# URLs base de la API de TMDB
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
RECOMMENDATIONS_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


# --- LÓGICA DE LA APLICACIÓN ---

@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations_list = []
    movie_title_from_user = ""
    error = None

    if request.method == 'POST':
        movie_title_from_user = request.form['movie_title']
        
        if not API_KEY:
            error = "Error de configuración del servidor: La clave de API no está definida."
        else:
            try:
                # 1. Buscar la película
                search_params = {'api_key': API_KEY, 'query': movie_title_from_user, 'language': 'es-ES'}
                response = requests.get(SEARCH_URL, params=search_params)
                response.raise_for_status()
                search_results = response.json()['results']
                
                if search_results:
                    first_movie_id = search_results[0]['id']
                    
                    # 2. Obtener las recomendaciones
                    recommendations_url = RECOMMENDATIONS_URL_TEMPLATE.format(movie_id=first_movie_id)
                    recs_params = {'api_key': API_KEY, 'language': 'es-ES'}
                    response = requests.get(recommendations_url, params=recs_params)
                    response.raise_for_status()
                    recommendations_results = response.json()['results']
                    
                    # Procesamos la lista
                    for movie_data in recommendations_results:
                        poster_path = movie_data.get('poster_path')
                        if poster_path:
                            full_poster_url = f"{IMAGE_BASE_URL}{poster_path}"
                        else:
                            full_poster_url = "https://via.placeholder.com/500x750?text=No+Poster"

                        recommendations_list.append({
                            'title': movie_data['title'],
                            'poster_url': full_poster_url
                        })
                else:
                    error = f"No se encontró ninguna película llamada '{movie_title_from_user}'."

            except requests.exceptions.RequestException as e:
                error = f"Ocurrió un error de comunicación con la API. Intenta de nuevo más tarde."
            except Exception as e:
                error = f"Ocurrió un error inesperado: {e}"

    return render_template('index.html', 
                           movie_title=movie_title_from_user, 
                           recommendations=recommendations_list,
                           error=error,
                           searched=request.method == 'POST')