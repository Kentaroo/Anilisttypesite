from flask import Flask

app = Flask(__name__)

# Test-Route
@app.route("/")
def home():
    return "<h1>Flask ist erfolgreich installiert! 🚀</h1>"

if __name__ == "__main__":
    app.run(debug=True)
