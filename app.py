from flask import Flask, render_template, request
import pandas as pd
import json
import ast

app = Flask(__name__)

# Indlæs CSV én gang når appen starter
df = pd.read_csv('movies_metadata.csv', low_memory=False)

from database import opret_tabel, gem_favorit, hent_favoritter, fjern_favorit, parse_genres

# Kald dette én gang når appen starter
opret_tabel()
favoritter = {}


def movie_dict(film):
    """Return a reusable film dictionary from a dataframe row."""
    return {
        'titel': film['title'],
        'rating': film['vote_average'],
        'aar': str(film['release_date'])[:4] if pd.notna(film['release_date']) else 'Unknown',
        'plakat': film['poster_path'],
        'genres': parse_genres(film['genres']),
        'beskrivelse': film['overview'] if pd.notna(film['overview']) else 'No description available.',
        'original_language': film['original_language'] if pd.notna(film['original_language']) else 'Unknown',
        'homepage': film['homepage'] if pd.notna(film['homepage']) and film['homepage'] != '' else None,
        'runtime': int(film['runtime']) if pd.notna(film['runtime']) else 'Unknown'
            #'adult': film['adult'] if pd.notna(film['adult']) else 'Unknown',
            #'collection': film['belongs_to_collection'] if pd.notna(film['belongs_to_collection']) else 'Unknown',
            #'budget': film['budget'] if pd.notna(film['budget']) else 'Unknown',
            #'id': film['id'] if pd.notna(film['id']) else 'Unknown',
            #imdb_id': film['imdb_id'] if pd.notna(film['imdb_id']) else 'Unknown',
            #'original_title': film['original_title'] if pd.notna(film['original_title']) else 'Unknown',
            #'popularity': film['popularity'] if pd.notna(film['popularity']) else 'Unknown',
            #'production_companies': film['production_companies'] if pd.notna(film['production_companies']) else 'Unknown',
            #'production_countries': film['production_countries'] if pd.notna(film['production_countries']) else 'Unknown',
            #'revenue': film['revenue'] if pd.notna(film['revenue']) else 'Unknown',
            #'spoken_languages': film['spoken_languages'] if pd.notna(film['spoken_languages']) else 'Unknown',
            #'status': film['status'] if pd.notna(film['status']) else 'Unknown',
            #'tagline': film['tagline'] if pd.notna(film['tagline']) else 'Unknown',
            #'video': film['video'] if pd.notna(film['video']) else 'Unknown' 
    }

def find_films(query, limit=50):
    query = query.strip()
    if not query:
        return []

    filter_title = df['title'].fillna('').str.contains(query, case=False, na=False)
    filter_original_title = df['original_title'].fillna('').str.contains(query, case=False, na=False)
    result_df = df[filter_title | filter_original_title].sort_values('vote_average', ascending=False)
    if limit is not None:
        result_df = result_df.head(limit)

    films = [movie_dict(film) for _, film in result_df.iterrows()]
    return films

def get_all_genres():
    """Extract all unique genres from the dataset."""
    all_genres = set()
    for genres_str in df['genres'].dropna():
        try:
            genres_list = ast.literal_eval(genres_str)
            if isinstance(genres_list, list):
                for g in genres_list:
                    if isinstance(g, dict) and 'name' in g:
                        all_genres.add(g['name'])
        except Exception:
            try:
                genres_list = json.loads(genres_str)
                if isinstance(genres_list, list):
                    for g in genres_list:
                        if isinstance(g, dict) and 'name' in g:
                            all_genres.add(g['name'])
            except Exception:
                pass
    return sorted(list(all_genres))

@app.route('/')
@app.route('/<int:page>')
def forside(page=1):
    # Get genre filter from query parameters
    selected_genres = request.args.getlist('genre')
    
    # Filtrer rækker med gyldige ratings og poster_path, sorter
    alle_film = (
        df[(df['vote_average'] > 0) & (df['poster_path'].notna()) & (df['vote_count'] > 100)]
        .sort_values('vote_average', ascending=False)
    )
    
    # Apply genre filter if genres are selected
    if selected_genres:
        filtered_films = []
        for _, film in alle_film.iterrows():
            genres_str = film['genres']
            try:
                genres_list = ast.literal_eval(genres_str) if isinstance(genres_str, str) else genres_str
            except Exception:
                try:
                    genres_list = json.loads(genres_str) if isinstance(genres_str, str) else genres_str
                except Exception:
                    genres_list = []
            
            if isinstance(genres_list, list):
                film_genres = [g.get('name') for g in genres_list if isinstance(g, dict) and 'name' in g]
                # Check if any selected genre matches the film's genres
                if any(genre in film_genres for genre in selected_genres):
                    filtered_films.append(film)
        
        alle_film = pd.DataFrame(filtered_films)
    
    # Pagination settings
    films_per_page = 20
    total_films = len(alle_film)
    total_pages = (total_films + films_per_page - 1) // films_per_page
    
    # Ensure page is valid
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages
    
    # Get films for current page
    start_idx = (page - 1) * films_per_page
    end_idx = start_idx + films_per_page
    filmliste = alle_film.iloc[start_idx:end_idx]

    # Byg en liste af dictionaries som HTML-skabelonen kan bruge
    film_data = [movie_dict(film) for _, film in filmliste.iterrows()]
    
    # Get all genres for the filter
    all_genres = get_all_genres()
    
    return render_template('index.html', film=film_data, current_page=page, total_pages=total_pages, 
                         all_genres=all_genres, selected_genres=selected_genres)

@app.route('/gem/<titel>')
def gem(titel):
    # Check om den er gemt
    if er_favorit(titel):
        return "Allerede gemt", 409
    
     # Find filmen sikkert
    film_match = df[df['title'] == titel]
    if film_match.empty:
        return "Film ikke fundet", 404

    film = film_match.iloc[0]
    
    gem_favorit(
        titel=film['title'],
        plakat_url=film['poster_path'],
        rating=film['vote_average'],
        aar=str(film['release_date'])[:4],
        original_language=film['original_language'] if pd.notna(film['original_language']) else 'Unknown',
        runtime=int(film['runtime']) if pd.notna(film['runtime']) else 'Unknown',
        genres=parse_genres(film['genres']),
        beskrivelse=film['overview'] if pd.notna(film['overview']) else 'No description available.',
        homepage=film['homepage'] if pd.notna(film['homepage']) and film['homepage'] != '' else None
    )
    return f'{titel} er gemt som favorit!', 200

def er_favorit(titel):
    favoritter = hent_favoritter()
    return any(f[1] == titel for f in favoritter)

@app.route('/favoritter')
def vis_favoritter():
    film = hent_favoritter()
    return render_template('favoritter.html', film=film, favoritter=favoritter)

@app.route('/api/search/html')
def api_search_html():
    query = request.args.get('query', '').strip()
    if not query:
        return '<p class="message">Indtast venligst en søgeterm.</p>'

    films = find_films(query, limit=20)
    if not films:
        return '<p class="message">Ingen film fundet.</p>'

    html = ''
    for f in films:
        html += render_template('film_card.html', f=f)
    return html

@app.route('/fjern/<titel>')
def fjern(titel):
    # Fjern fra database / liste
    print("Fjerner:", titel)
    fjern_favorit(titel)
    return '', 200

@app.route("/gem", methods=["POST"])
def gem_favorit():
    data = request.get_json()
    titel = data.get("titel")
    note = data.get("note")

    # eksempel: gem i liste/dictionary
    if titel in favoritter:
        return "", 409

    favoritter[titel] = note  # gem note sammen med titel

    return "", 200

@app.route('/søg')
def søg():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', default=1, type=int)
    films = []
    total_pages = 0
    if query:
        all_results = find_films(query, limit=None)
        films_per_page = 20
        total_results = len(all_results)
        total_pages = (total_results + films_per_page - 1) // films_per_page
        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages
        start_idx = (page - 1) * films_per_page
        end_idx = start_idx + films_per_page
        films = all_results[start_idx:end_idx]

    return render_template('søg.html', film=films, query=query, current_page=page, total_pages=total_pages)

@app.route('/genrer')
def genrer():
    """Display all genres."""
    all_genres = get_all_genres()
    return render_template('genre_filter.html', all_genres=all_genres, selected_genres=[])

@app.route('/filter/genre/<genre>')
def filter_by_genre(genre):
    """Filter movies by genre."""
    movies_with_genre = []
    
    for _, film in df.iterrows():
        genres_str = film['genres']
        try:
            genres_list = ast.literal_eval(genres_str) if isinstance(genres_str, str) else genres_str
        except Exception:
            try:
                genres_list = json.loads(genres_str) if isinstance(genres_str, str) else genres_str
            except Exception:
                genres_list = []
        
        if isinstance(genres_list, list):
            for g in genres_list:
                if isinstance(g, dict) and g.get('name') == genre:
                    movies_with_genre.append(movie_dict(film))
                    break
    
    # Sort by rating
    movies_with_genre.sort(key=lambda x: x['rating'], reverse=True)
    return render_template('genre_results.html', films=movies_with_genre, genre=genre)

if __name__ == '__main__':
    app.run(debug=True, port=8000)