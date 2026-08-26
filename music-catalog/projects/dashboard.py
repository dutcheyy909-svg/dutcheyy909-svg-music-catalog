from flask import Flask, render_template, jsonify
import json
from pathlib import Path

app = Flask(__name__)

def load_metadata():
    base = Path(".")

    # Adjust filenames if yours differ
    songtradr = json.load(open(base / "Songtradr.json"))
    audiosparx = json.load(open(base / "AudioSparx.json"))
    ringo = json.load(open(base / "Ringo.json"))
    spotify = json.load(open(base / "SpotifyFeatures.json"))  # or CSV → JSON if you prefer

    return {
        "songtradr": songtradr,
        "audiosparx": audiosparx,
        "ringo": ringo,
        "spotify": spotify
    }

@app.route("/")
def index():
    data = load_metadata()
    return render_template("index.html", data=data)

@app.route("/api/data")
def api_data():
    return jsonify(load_metadata())

if __name__ == "__main__":
    app.run(debug=True)
