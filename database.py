import sqlite3

def get_connection():
    """Returnerer en forbindelse til databasen."""
    return sqlite3.connect('favoritter.db')

def opret_tabel():
    """Opretter tabellen hvis den ikke allerede findes."""
    con = get_connection()
    con.execute('''
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
                    homepage TEXT
                    )
                    ''')
    con.commit()
    con.close()

def gem_favorit(titel, plakat_url, rating, aar, original_language, runtime, genres, beskrivelse, homepage):
    """Gemmer en film som favorit."""
    con = get_connection()
    con.execute(
        'INSERT INTO favoritter (titel, plakat_url, rating, aar, original_language, runtime, genres, beskrivelse, homepage) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (titel, plakat_url, rating, aar, original_language, runtime, genres, beskrivelse, homepage)
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
    return rows