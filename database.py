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
                    aar TEXT
                    )
                    ''')
    con.commit()
    con.close()

def gem_favorit(titel, plakat_url, rating, aar):
    """Gemmer en film som favorit."""
    con = get_connection()
    con.execute(
        'INSERT INTO favoritter (titel, plakat_url, rating, aar) VALUES(?, ?, ?, ?)',
        (titel, plakat_url, rating, aar)
        )
    con.commit()
    con.close()

def hent_favoritter():
    """Returnerer alle gemte favoritter som en liste."""
    con = get_connection()
    rows = con.execute('SELECT * FROM favoritter').fetchall()
    con.close()
    return rows