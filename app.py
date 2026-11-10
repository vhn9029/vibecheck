# Allows Python to work with SQLite
import sqlite3
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Store the database beside app.py.
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "vibecheck.db"

MOODS = {
    "Happy",
    "Sad",
    "Relaxed",
    "Energetic",
    "Nostalgic",
    "Stressed",
}


# Create the database and entries table if it doesn't exist.
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        #Defines how journal entries are stored. 
        conn.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song TEXT NOT NULL,
                artist TEXT NOT NULL,
                mood TEXT NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Music Journal page
@app.route("/journal", methods=["GET", "POST"])
def journal():

    if request.method == "POST":
        song = request.form.get("song", "").strip()
        artist = request.form.get("artist", "").strip()
        mood = request.form.get("mood", "").strip()
        note = request.form.get("note", "").strip()

        # Validate the submitted information.
        if (
            not song
            or not artist
            or mood not in MOODS
            or len(song) > 150
            or len(artist) > 150
            or len(note) > 1000
        ):
            return render_template(
                "journal.html",
                error="Please check your entry and try again."
            ), 400

        try:
            # Save the entry to SQLite.
            with sqlite3.connect(DATABASE) as conn:
                # Saves new journal entries.
                # '?' are placeholders so the values safely pass user information to SQL.
                conn.execute(
                    """
                    INSERT INTO journal_entries
                    (song, artist, mood, note)
                    VALUES (?, ?, ?, ?)
                    """,
                    (song, artist, mood, note)
                )

        # Handles database errors. 
        except sqlite3.Error:
            app.logger.exception("Unable to save journal entry")
            return render_template(
                "journal.html",
                error="Your entry could not be saved. Please try again."
            ), 500

        # Only show success after saving to the database.
        return render_template(
            "journal.html",
            # Displays confirmation after saving. 
            message="Entry saved successfully!"
        )

    return render_template("journal.html")



# Journal History page
@app.route("/history")
def history():

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        entries = conn.execute(
            """
            SELECT id, song, artist, mood, note, created_at
            FROM journal_entries
            ORDER BY id DESC
            """
        ).fetchall()

    return render_template(
        "history.html",
        entries=entries
    )


# Delete a journal entry
@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):

    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            "DELETE FROM journal_entries WHERE id = ?",
            (entry_id,)
        )

    return redirect(url_for("history"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
