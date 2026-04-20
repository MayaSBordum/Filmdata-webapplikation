from flask import Flask, render_template, jsonify, request
import pandas as pd
import sqlite3
from flask import redirect

app = Flask(__name__)

# Indlæs CSV én gang når appen starter
df = pd.read_csv('movies_metadata.csv', low_memory=False)

from database import opret_tabel, gem_favorit, hent_favoritter, fjern_favorit

# Kald dette én gang når appen starter
opret_tabel()

def find_films(query, limit=50):
    query = query.strip()
    if not query:
        return []

    filter_title = df['title'].fillna('').str.contains(query, case=False, na=False)
    filter_original_title = df['original_title'].fillna('').str.contains(query, case=False, na=False)
    result_df = df[filter_title | filter_original_title].sort_values('vote_average', ascending=False).head(limit)

    films = []
    for _, film in result_df.iterrows():
        films.append({
            'titel': film['title'],
            'rating': film['vote_average'],
            'aar': str(film['release_date'])[:4] if pd.notna(film['release_date']) else 'Unknown',
            'plakat': film['poster_path'],
            'genres': film['genres'] if pd.notna(film['genres']) else 'No genres available.',
            'beskrivelse': film['overview'] if pd.notna(film['overview']) else 'No description available.',
            'original_language': film['original_language'] if pd.notna(film['original_language']) else 'Unknown',
            'homepage': film['homepage'] if pd.notna(film['homepage']) and film['homepage'] != '' else None,
            'runtime': int(film['runtime']) if pd.notna(film['runtime']) else 'Unknown'
        })

    return films

@app.route('/')
def forside():
    # Filtrer rækker med gyldige ratings og poster_path, sorter
    filmliste = (
        df[(df['vote_average'] > 0) & (df['poster_path'].notna()) & (df['vote_count'] > 100)]
        .sort_values('vote_average', ascending=False)
        .head(20)
    )


    # Byg en liste af dictionaries som HTML-skabelonen kan bruge
    film_data = []
    for _, film in filmliste.iterrows():
        film_data.append({
            'titel': film['title'],
            'rating': film['vote_average'],
            'aar': str(film['release_date'])[:4] if pd.notna(film['release_date']) else 'Unknown',
            'plakat': film['poster_path'],
            'genres': film['genres'] if pd.notna(film['genres']) else 'No genres available.',
            
            'beskrivelse': film['overview'] if pd.notna(film['overview']) else 'No description available.',
            'original_language': film['original_language'] if pd.notna(film['original_language']) else 'Unknown',
            'homepage': film['homepage'] if pd.notna(film['homepage']) and film['homepage'] != '' else None,
            'runtime': int(film['runtime']) if pd.notna(film['runtime']) else 'Unknown',

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
        })

    return render_template('index.html', film=film_data)

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
        genres=film['genres'] if pd.notna(film['genres']) else 'No genres available.',
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

    films = find_films(query)
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
    films = find_films(query) if query else None
    return render_template('søg.html', film=films, query=query)

if __name__ == '__main__':
    app.run(debug=True, port=8000)