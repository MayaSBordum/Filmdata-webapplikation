from flask import Flask, render_template, request
import pandas as pd
import json
import ast

app = Flask(__name__)

# Indlæs CSV én gang når appen starter
df = pd.read_csv('movies_metadata.csv', low_memory=False)

from database import opret_tabel, gem_favorit, hent_favoritter, fjern_favorit

# Kald dette én gang når appen starter
opret_tabel()

def parse_genres(genres_str):
    """Parse genres field and return comma-separated names."""
    if not pd.notna(genres_str) or genres_str == '':
        return 'No genres available.'
    genres_list = None
    try:
        genres_list = ast.literal_eval(genres_str)
    except Exception:
        try:
            genres_list = json.loads(genres_str)
        except Exception:
            return 'No genres available.'
    if not isinstance(genres_list, list):
        return 'No genres available.'
    genre_names = [g.get('name') for g in genres_list if isinstance(g, dict) and 'name' in g]
    return ', '.join(genre_names) if genre_names else 'No genres available.'


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

@app.route('/')
@app.route('/<int:page>')
def forside(page=1):
    # Filtrer rækker med gyldige ratings og poster_path, sorter
    alle_film = (
        df[(df['vote_average'] > 0) & (df['poster_path'].notna()) & (df['vote_count'] > 100)]
        .sort_values('vote_average', ascending=False)
    )
    
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
    return render_template('index.html', film=film_data, current_page=page, total_pages=total_pages)

@app.route('/gem/<titel>')
def gem(titel):
    # Find filmen i CSV-filen
    film = df[df['title'] == titel].iloc[0]
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
    return f'{titel} er gemt som favorit!'

@app.route('/favoritter')
def vis_favoritter():
    film = hent_favoritter()
    return render_template('favoritter.html', film=film)

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

if __name__ == '__main__':
    app.run(debug=True, port=8000)