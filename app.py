
import pyodbc

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

app = Flask(__name__)


# SQL Server connection settings
def get_db_connection():
    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        r"SERVER=localhost\SQLEXPRESS;"
        "DATABASE=VibeCheckDB;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string, timeout=5)


# Allowed moods
MOODS = {
    "Happy",
    "Sad",
    "Relaxed",
    "Energetic",
    "Nostalgic",
    "Stressed"
}


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

        # Validate form information
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

        connection = None

        try:
            # Connect to SQL Server
            connection = get_db_connection()
            cursor = connection.cursor()

            # Save journal entry
            cursor.execute(
                """
                INSERT INTO dbo.journal_entries
                (song, artist, mood, note)
                VALUES (?, ?, ?, ?)
                """,
                song, artist, mood, note
            )

            # Commit the database transaction
            connection.commit()

        except pyodbc.Error:
            if connection is not None:
                connection.rollback()

            app.logger.exception("Unable to save entry")

            return render_template(
                "journal.html",
                error="Unable to save entry. Please try again."
            ), 500

        finally:
            if connection is not None:
                connection.close()

        # Success appears only after the database commit
        return render_template(
            "journal.html",
            message="Entry saved successfully!"
        )

    return render_template("journal.html")


# Journal History page
@app.route("/history")
def history():

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, song, artist, mood, note, created_at
            FROM dbo.journal_entries
            ORDER BY id DESC
            """
        )

        # Convert SQL Server rows to dictionaries
        columns = [column[0] for column in cursor.description]
        entries = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    except pyodbc.Error:
        app.logger.exception("Unable to load journal history")

        return render_template(
            "history.html",
            entries=[],
            error="Unable to load journal history."
        ), 500

    finally:
        if connection is not None:
            connection.close()

    return render_template(
        "history.html",
        entries=entries
    )


# Delete a journal entry
@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM dbo.journal_entries WHERE id = ?",
            entry_id
        )

        connection.commit()

    except pyodbc.Error:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Unable to delete entry")
        return "Unable to delete journal entry.", 500

    finally:
        if connection is not None:
            connection.close()

    return redirect(url_for("history"))


# Music Statistics Dashboard
@app.route("/dashboard")
def dashboard():
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Count all saved journal entries
        cursor.execute(
            "SELECT COUNT(*) FROM dbo.journal_entries"
        )
        total_entries = cursor.fetchone()[0]

        # Find the most frequently recorded mood
        cursor.execute("""
            SELECT TOP (1) mood, COUNT(*) AS mood_count
            FROM dbo.journal_entries
            GROUP BY mood
            ORDER BY mood_count DESC, mood ASC
        """)

        row = cursor.fetchone()
        top_mood = row[0] if row else "None yet"

        # Find the most frequently recorded artist
        cursor.execute("""
            SELECT TOP (1) artist, COUNT(*) AS artist_count
            FROM dbo.journal_entries
            GROUP BY artist
            ORDER BY artist_count DESC, artist ASC
        """)

        row = cursor.fetchone()
        top_artist = row[0] if row else "None yet"

        # Calculate the breakdown of moods
        cursor.execute("""
            SELECT mood, COUNT(*) AS mood_count
            FROM dbo.journal_entries
            GROUP BY mood
            ORDER BY mood_count DESC, mood ASC
        """)

        mood_breakdown = []

        for row in cursor.fetchall():
            count = row[1]

            percentage = (
                round(count / total_entries * 100, 1)
                if total_entries > 0 else 0
            )

            mood_breakdown.append({
                "name": row[0],
                "count": count,
                "percentage": percentage
            })

        return render_template(
            "dashboard.html",
            total_entries=total_entries,
            top_mood=top_mood,
            top_artist=top_artist,
            mood_breakdown=mood_breakdown
        )

    except pyodbc.Error:
        app.logger.exception(
            "Unable to load music statistics"
        )

        return render_template(
            "dashboard.html",
            error="Unable to load dashboard statistics.",
            total_entries=0,
            top_mood="Unavailable",
            top_artist="Unavailable",
            mood_breakdown=[]
        ), 500

    finally:
        if connection is not None:
            connection.close()

if __name__ == "__main__":
    app.run(debug=True)
