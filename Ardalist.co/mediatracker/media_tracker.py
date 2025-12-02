from flask import Flask, request, render_template, redirect, url_for
import json
import os

# Flask-App erstellen
app = Flask(__name__)

# Dynamischer Pfad zur JSON-Datenbank
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")


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

# Route: Hauptseite
@app.route("/")
def home():
    # Lade Medien-Daten aus der JSON-Datenbank
    database = load_database()
    return render_template("index.html", media_entries=database)

# Route: Eintrag hinzufügen
@app.route("/add", methods=["POST"])
def add_entry():
    if request.method == "POST":
        # Formulardaten abrufen
        title = request.form["title"]
        media_type = request.form["type"]
        status = request.form["status"]

        # JSON-Datenbank aktualisieren
        database = load_database()
        new_entry = {
            "title": title,
            "type": media_type,
            "status": status
        }
        database.append(new_entry)
        save_database(database)

        # Nach Hinzufügen zur Hauptseite weiterleiten
        return redirect(url_for("home"))
    else:
        return "Nur POST-Anfragen erlaubt!"

# Flask Server starten
if __name__ == "__main__":
    # Starte den Flask-Server im Debug-Modus
    app.run(debug=True)
