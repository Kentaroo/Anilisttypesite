from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import json
import os
import uuid  # Für einzigartige Dateinamen
import random
from werkzeug.utils import secure_filename  # Sicherheit beim Speichern von Dateien

# ===========================
#  FLASK-APP INITIALISIERUNG
# ===========================
app = Flask(__name__)

# ===========================
#  KONFIGURATION
# ===========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Aktueller Pfad
DB_FILE = os.path.join(BASE_DIR, "database.json")      # JSON-Datenbank
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")      # Ordner für Uploads
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}    # Erlaubte Bilder

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Sicherstellen, dass der Upload-Ordner existiert
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===========================
#  HILFSFUNKTIONEN
# ===========================

def load_database():
    """Lädt die Datenbank aus der JSON-Datei."""
    try:
        with open(DB_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_database(data):
    """Speichert die Datenbank in die JSON-Datei."""
    with open(DB_FILE, "w") as file:
        json.dump(data, file, indent=4)

def allowed_file(filename):
    """Prüft, ob die Datei erlaubt ist (Extension)."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ===========================
#  ROUTES
# ===========================

# --------- Home / Übersicht ---------
@app.route("/")
def home():
    """
    Zeigt die Startseite an.
    Randomisiert die Medieneinträge.
    Beinhaltet auch das Add-Formular.
    """
    database = load_database()
    random_entries = database.copy()
    random.shuffle(random_entries)
    random_entries = random_entries[:12]  # Nur 12 Einträge wie AniList
    return render_template("index.html", media_entries=random_entries)

# --------- Eintrag hinzufügen ---------
@app.route("/add", methods=["POST"])
def add_entry():
    """
    Fügt einen neuen Eintrag hinzu (Titel, Typ, Status, Bild optional)
    """
    title = request.form["title"]
    media_type = request.form["type"]
    status = request.form["status"]
    image = request.files.get("image")

    database = load_database()

    # Prüfen, ob Eintrag schon existiert
    if any(entry["title"].lower() == title.lower() for entry in database):
        return "Eintrag existiert bereits! <a href='/'>Zurück</a>"

    # Bild speichern, falls vorhanden
    image_filename = None
    if image and image.filename and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_filename = f"{uuid.uuid4()}_{filename}"
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

    # Neuer Eintrag in DB
    database.append({
        "title": title,
        "type": media_type,
        "status": status,
        "image": image_filename
    })
    save_database(database)

    return redirect(url_for("home"))

# --------- Bilder laden ---------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Gibt hochgeladene Bilder aus dem Upload-Ordner zurück."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------- Eintrag löschen ---------
@app.route("/delete/<int:index>", methods=["POST"])
def delete_entry(index):
    """
    Löscht einen Eintrag anhand des Index.
    Entfernt auch das Bild aus dem Upload-Ordner.
    """
    database = load_database()
    if 0 <= index < len(database):
        entry = database.pop(index)
        if entry.get("image"):
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], entry["image"])
            if os.path.exists(image_path):
                os.remove(image_path)
        save_database(database)
        return redirect(url_for("home"))
    return "Ungültiger Index! <a href='/'>Zurück</a>"

# --------- Eintrag bearbeiten ---------
@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit_entry(index):
    """
    GET: Zeigt das Bearbeitungsformular
    POST: Speichert Änderungen
    """
    database = load_database()
    if not (0 <= index < len(database)):
        return "Ungültiger Index! <a href='/'>Zurück</a>"

    if request.method == "POST":
        database[index]["title"] = request.form["title"]
        database[index]["type"] = request.form["type"]
        database[index]["status"] = request.form["status"]
        save_database(database)
        return redirect(url_for("home"))

    return render_template("edit.html", entry=database[index], index=index)

# --------- Suche ---------
@app.route("/search", methods=["GET", "POST"])
def search_entries():
    """
    Sucht nach Medieneinträgen.
    Filterbar nach title, type oder status.
    """
    database = load_database()
    results = None
    query = ""
    filter_by = "title"

    if request.method == "POST":
        query = request.form["query"]
        filter_by = request.form["filter_by"]
        results = [
            entry for entry in database
            if query.lower() in entry.get(filter_by, "").lower()
        ]

    return render_template("search.html", results=results, query=query, filter_by=filter_by)

# --------- Stats (nur Profil) ---------
@app.route("/stats")
def stats():
    """
    Zeigt Statistiken nach Typ und Status an.
    Nur auf Profilseite relevant.
    """
    database = load_database()
    stats_by_type = {}
    stats_by_status = {}

    for entry in database:
        stats_by_type[entry["type"]] = stats_by_type.get(entry["type"], 0) + 1
        stats_by_status[entry["status"]] = stats_by_status.get(entry["status"], 0) + 1

    return render_template(
        "stats.html",
        stats_by_type=stats_by_type,
        stats_by_status=stats_by_status,
        total_entries=len(database)
    )

# --------- Profilseite ---------
@app.route("/profile")
def profile():
    """
    Zeigt Profilseite mit:
    - Banner/Header
    - Stats
    - Activity
    - Editierbare Sidebar (später)
    """
    database = load_database()
    random_activity = database.copy()
    random.shuffle(random_activity)
    random_activity = random_activity[:6]  # Letzte Aktivitäten (randomisiert)

    return render_template(
        "profile.html",
        activity=random_activity
    )

# ===========================
#  FLASK SERVER START
# ===========================
if __name__ == "__main__":
    app.run(debug=True)
