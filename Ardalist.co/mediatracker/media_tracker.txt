from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import json
import os
import uuid  # Für einzigartige Dateinamen
from werkzeug.utils import secure_filename  # Sicherheit beim Speichern von Dateien

# Flask-App erstellen
app = Flask(__name__)

# Dynamischer Pfad zur JSON-Datenbank
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")

# Ordner für hochgeladene Bilder
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Stelle sicher, dass der Upload-Ordner existiert
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Erlaubte Dateitypen für den Upload
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


# JSON-Daten laden
def load_database():
    try:
        with open(DB_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# JSON-Daten speichern
def save_database(data):
    with open(DB_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Prüfen, ob Datei erlaubt ist
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Route: Hauptseite
@app.route("/")
def home():
    database = load_database()
    return render_template("index.html", media_entries=database)

# Route: Eintrag hinzufügen
@app.route("/add", methods=["POST"])
def add_entry():
    if request.method == "POST":
        title = request.form["title"]
        media_type = request.form["type"]
        status = request.form["status"]
        image = request.files["image"]  # Datei-Upload-Handling

        # Prüfe, ob der Titel bereits existiert
        database = load_database()
        for entry in database:
            if entry["title"].lower() == title.lower():
                return "Eintrag existiert bereits! <a href='/'>Zurück</a>"

        # Bild speichern (falls hochgeladen)
        image_path = None
        if image and image.filename != "" and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
            image.save(image_path)

        # JSON-Datenbank aktualisieren
        new_entry = {
            "title": title,
            "type": media_type,
            "status": status,
            "image": unique_filename if image_path else None
        }
        database.append(new_entry)
        save_database(database)

        return redirect(url_for("home"))
    else:
        return "Nur POST-Anfragen erlaubt!"

# Route: Bilder laden
@app.route("/uploads/<filename>")
def get_uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Route: Eintrag löschen
@app.route("/delete/<int:index>", methods=["POST"])
def delete_entry(index):
    database = load_database()
    if 0 <= index < len(database):
        removed_entry = database.pop(index)
        # Lösche das zugehörige Bild (falls vorhanden)
        if "image" in removed_entry and removed_entry["image"]:
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], removed_entry["image"])
            if os.path.exists(image_path):
                os.remove(image_path)
        save_database(database)
        return redirect(url_for("home"))
    else:
        return "Ungültiger Index! <a href='/'>Zurück</a>"

# Route: Eintrag bearbeiten - Formular anzeigen
@app.route("/edit/<int:index>")
def edit_entry_view(index):
    database = load_database()
    if 0 <= index < len(database):
        entry = database[index]
        return render_template("edit.html", entry=entry, index=index)
    else:
        return "Ungültiger Index! <a href='/'>Zurück</a>"

# Route: Eintrag bearbeiten - Aktualisierung abschließen
@app.route("/edit/<int:index>", methods=["POST"])
def edit_entry(index):
    database = load_database()
    if 0 <= index < len(database):
        entry = database[index]
        entry["title"] = request.form["title"]
        entry["type"] = request.form["type"]
        entry["status"] = request.form["status"]
        save_database(database)
        return redirect(url_for("home"))
    else:
        return "Ungültiger Index! <a href='/'>Zurück</a>"

# Route: Suche
@app.route("/search", methods=["GET", "POST"])
def search_entries():
    database = load_database()
    if request.method == "POST":
        query = request.form["query"]  # Suchbegriff
        filter_by = request.form["filter_by"]  # Filterkriterium (title, type, status)

        # Filtere die Einträge basierend auf dem Suchkriterium
        results = [
            entry for entry in database
            if query.lower() in entry[filter_by].lower()
        ]
        return render_template("search.html", results=results, query=query, filter_by=filter_by)
    else:
        return render_template("search.html", results=None)

# Route: Statistiken
@app.route("/stats")
def stats():
    database = load_database()
    stats_by_type = {}
    stats_by_status = {}
    for entry in database:
        media_type = entry["type"]
        stats_by_type[media_type] = stats_by_type.get(media_type, 0) + 1
        status = entry["status"]
        stats_by_status[status] = stats_by_status.get(status, 0) + 1
    return render_template(
        "stats.html",
        stats_by_type=stats_by_type,
        stats_by_status=stats_by_status,
        total_entries=len(database)
    )

# Flask Server starten
if __name__ == "__main__":
    app.run(debug=True)
