from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# Indlæs CSV én gang når appen starter
df = pd.read_csv('movies_metadata.csv', low_memory=False)

from database import opret_tabel, gem_favorit, hent_favoritter

# Kald dette én gang når appen starter
opret_tabel()

@app.route('/')
def forside():
    # Filtrer rækker med gyldige ratings og poster_path, sorter
    filmliste = (
        df[(df['vote_average'] > 0) & (df['poster_path'].notna())]
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
        aar=str(film['release_date'])[:4]
    )
    return f'{titel} er gemt som favorit!'

@app.route('/favoritter')
def vis_favoritter():
    film = hent_favoritter()
    return render_template('favoritter.html', film=film)

if __name__ == '__main__':
    app.run(debug=True)