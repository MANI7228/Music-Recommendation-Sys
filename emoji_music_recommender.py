#!/usr/bin/env python3
"""
A simple emoji‑based music recommendation system implemented in Python.

This script demonstrates how the core features of the original Java Swing
application from the "Major‑Project" repository can be built using Python.

Features:

- Uses SQLite (a lightweight file‑based database) instead of MySQL.
- Provides a command‑line interface for signing up, logging in, and
  selecting an emoji to receive music recommendations.
- Stores users, emojis and songs in relational tables similar to the
  original project's schema.
- Demonstrates how to map emojis to recommended songs.

Usage:

  $ python3 emoji_music_recommender.py

The script will prompt you to either sign up or log in. After a successful
login, you will be shown a list of available emojis. Pick an emoji by its
ID to see a set of recommended songs associated with it.

The database is initialised on first run with a few sample records. Feel
free to modify the `INITIAL_EMOJIS` and `INITIAL_SONGS` dictionaries to
customise the library of emojis and songs.
"""
import sqlite3
import getpass
from pathlib import Path

# Path to the SQLite database (in the same directory as this script)
DB_PATH = Path(__file__).with_suffix('.db')

# Initial data used to seed the database on first run
INITIAL_EMOJIS = [
    (1, "Happy", "😊"),
    (2, "Sad",   "😢"),
    (3, "Angry", "😠"),
    (4, "Love",  "😍"),
]

INITIAL_SONGS = [
    # id, author, movie_name/description, music_producer/fullLyrics, name, singer
    (1, "John Williams", "A New Hope", "London Symphony Orchestra", "Star Wars Theme", "London Symphony Orchestra"),
    (2, "Ludovico Einaudi", "Night", "Decca Records", "Nuvole Bianche", "Ludovico Einaudi"),
    (3, "Adele", "21", "Paul Epworth", "Rolling in the Deep", "Adele"),
    (4, "Pharrell Williams", "Happy", "Pharrell Williams", "Happy", "Pharrell Williams"),
    (5, "Bill Withers", "+", "Bill Withers", "Ain't No Sunshine", "Bill Withers"),
]

# Mapping of emoji_id to song IDs
# e.g., the "happy" emoji maps to songs 4 and 1; the "sad" emoji maps to songs 2 and 5, etc.
INITIAL_EMOJI_SONG_MAP = {
    1: [4, 1],  # Happy maps to "Happy" and "Star Wars Theme"
    2: [2, 5],  # Sad maps to "Nuvole Bianche" and "Ain't No Sunshine"
    3: [3],     # Angry maps to "Rolling in the Deep"
    4: [2, 4],  # Love maps to "Nuvole Bianche" and "Happy"
}


def get_db_connection():
    """Return a connection to the SQLite database, creating tables if necessary."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    create_tables_if_needed(conn)
    return conn


def create_tables_if_needed(conn):
    """Create the tables for users, emojis, songs and mappings if they don't exist."""
    c = conn.cursor()

    # Users table similar to signuppage1 in Java version
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT
        )
        """
    )

    # Emojis table similar to emoji1 in Java version
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS emojis (
            emoji_id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            emoji TEXT NOT NULL
        )
        """
    )

    # Songs table similar to songs table in Java version
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY,
            author TEXT,
            movie_name TEXT,
            music_producer TEXT,
            name TEXT,
            singer TEXT
        )
        """
    )

    # Mapping table between emoji and song (similar to emoji_song_mappings)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS emoji_song_mappings (
            emoji_id INTEGER,
            song_id INTEGER,
            FOREIGN KEY (emoji_id) REFERENCES emojis(emoji_id),
            FOREIGN KEY (song_id) REFERENCES songs(id)
        )
        """
    )

    conn.commit()

    # If the emojis table is empty, insert initial data
    if c.execute("SELECT COUNT(*) FROM emojis").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO emojis (emoji_id, description, emoji) VALUES (?, ?, ?)",
            INITIAL_EMOJIS,
        )
        conn.commit()

    # If the songs table is empty, insert sample songs
    if c.execute("SELECT COUNT(*) FROM songs").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO songs (id, author, movie_name, music_producer, name, singer)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            INITIAL_SONGS,
        )
        conn.commit()

    # If the mapping table is empty, insert the initial emoji‑song relations
    if c.execute("SELECT COUNT(*) FROM emoji_song_mappings").fetchone()[0] == 0:
        mapping_entries = [
            (emoji_id, song_id)
            for emoji_id, song_ids in INITIAL_EMOJI_SONG_MAP.items()
            for song_id in song_ids
        ]
        c.executemany(
            "INSERT INTO emoji_song_mappings (emoji_id, song_id) VALUES (?, ?)",
            mapping_entries,
        )
        conn.commit()


# -- User management functions --------------------------------------------------

def sign_up(conn):
    """Register a new user by collecting email, password, age and gender."""
    email = input("Enter email: ").strip()
    while True:
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password == confirm_password:
            break
        print("Passwords do not match. Please try again.")

    age_input = input("Enter age (optional): ").strip()
    age = int(age_input) if age_input.isdigit() else None
    gender = input("Enter gender (optional): ").strip() or None

    try:
        conn.execute(
            "INSERT INTO users (email, password, age, gender) VALUES (?, ?, ?, ?)",
            (email, password, age, gender),
        )
        conn.commit()
        print("Signup successful. You can now log in.")
    except sqlite3.IntegrityError:
        print("A user with this email already exists. Please try another email.")


def log_in(conn):
    """Authenticate a user based on email and password."""
    email = input("Enter email: ").strip()
    password = getpass.getpass("Enter password: ")
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?", (email, password)
    )
    user = c.fetchone()
    if user:
        print(f"Login successful. Welcome, {user['email']}!")
        return user
    else:
        print("Login failed. Invalid credentials.")
        return None


# -- Emoji and song recommendation functions ----------------------------------

def display_emojis(conn):
    """Display all available emojis to the user."""
    c = conn.cursor()
    emojis = c.execute("SELECT emoji_id, description, emoji FROM emojis").fetchall()
    print("\nAvailable Emojis:")
    print("ID  | Emoji | Description")
    print("----+-------+------------")
    for row in emojis:
        print(f"{row['emoji_id']:>2}  | {row['emoji']}    | {row['description']}")


def get_songs_for_emoji(conn, emoji_id):
    """Retrieve a list of songs mapped to a given emoji ID."""
    c = conn.cursor()
    songs = c.execute(
        """
        SELECT s.id, s.name, s.singer, s.author, s.movie_name, s.music_producer
        FROM songs s
        JOIN emoji_song_mappings m ON s.id = m.song_id
        WHERE m.emoji_id = ?
        """,
        (emoji_id,),
    ).fetchall()
    return songs


def show_song_recommendations(conn):
    """Prompt the user to pick an emoji and display associated songs."""
    display_emojis(conn)
    choice = input("\nEnter the ID of the emoji you feel like: ").strip()
    if not choice.isdigit():
        print("Invalid input. Please enter a numeric emoji ID.")
        return
    emoji_id = int(choice)

    songs = get_songs_for_emoji(conn, emoji_id)
    if not songs:
        print("No songs found for the selected emoji.")
    else:
        print("\nRecommended Songs:")
        print("ID  | Song Name           | Singer              | Author/Producer")
        print("----+----------------------+----------------------+----------------------")
        for song in songs:
            print(
                f"{song['id']:>2}  | {song['name'][:20]:<20} | "
                f"{song['singer'][:20]:<20} | "
                f"{song['author'][:20]:<20}"
            )


# -- Main application loop ------------------------------------------------------

def main():
    conn = get_db_connection()
    print("\nWelcome to the Emoji‑Based Music Recommender!")
    while True:
        print("\nMain Menu:")
        print("1. Sign Up")
        print("2. Log In")
        print("3. Exit")
        choice = input("Select an option: ").strip()
        if choice == '1':
            sign_up(conn)
        elif choice == '2':
            user = log_in(conn)
            if user:
                # After successful login, allow song recommendations
                while True:
                    print("\nChoose an action:")
                    print("1. Get song recommendations by emoji")
                    print("2. Log out")
                    sub_choice = input("Select an option: ").strip()
                    if sub_choice == '1':
                        show_song_recommendations(conn)
                    elif sub_choice == '2':
                        break
                    else:
                        print("Invalid choice. Please try again.")
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

    conn.close()


if __name__ == '__main__':
    main()
