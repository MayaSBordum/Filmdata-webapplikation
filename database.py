import sqlite3
import ast
import json
import pandas as pd

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

def get_connection():
    """Returnerer en forbindelse til databasen."""
    return sqlite3.connect('favoritter.db')

def opret_tabel():
    conn = sqlite3.connect("favoritter.db")
    cur = conn.cursor()
    """Opretter tabellen hvis den ikke allerede findes."""
    con = get_connection()
    cur.execute('''
                CREATE TABLE IF NOT EXISTS favoritter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titel TEXT NOT NULL,
                    plakat_url TEXT,
                    rating REAL,
                    aar TEXT,
                    original_language TEXT,
                    runtime INTEGER,
                    genres TEXT,
                    beskrivelse TEXT,
                    homepage TEXT,
                    note TEXT
                    )
                    ''')

def gem_favorit(titel, plakat_url, rating, aar, original_language, runtime, genres, beskrivelse, homepage, note=None):
    """Gemmer en film som favorit."""
    con = get_connection()
    con.execute(
        'INSERT INTO favoritter (titel, plakat_url, rating, aar, original_language, runtime, genres, beskrivelse, homepage, note) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (titel, plakat_url, rating, aar, original_language, runtime, genres, beskrivelse, homepage, note)
        )
    con.commit()
    con.close()

def fjern_favorit(titel):
    """Fjerner en film fra favoritter baseret på titel."""
    con = get_connection()
    con.execute(
        'DELETE FROM favoritter WHERE titel = ?',
        (titel,)
    )
    con.commit()
    con.close()

def hent_favoritter():
    """Returnerer alle gemte favoritter som en liste."""
    con = get_connection()
    rows = con.execute('SELECT * FROM favoritter').fetchall()
    con.close()
    # Parse genres if it's raw JSON-like string
    parsed_rows = []
    for row in rows:
        row_list = list(row)
        genres = row_list[7]  # genres is at index 7
        if genres and genres.startswith('['):
            row_list[7] = parse_genres(genres)
        parsed_rows.append(tuple(row_list))
    return parsed_rows

def opdater_note(titel, note):
    conn = sqlite3.connect("favoritter.db")
    cur = conn.cursor()
    cur.execute("UPDATE favoritter SET note=? WHERE titel=?", (note, titel))
    conn.commit()
    conn.close()