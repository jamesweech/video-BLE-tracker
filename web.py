from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Path to the tag states JSON file
STATE_FILE = "tag_states.json"

def load_tag_states():
    """Load the current tag states from the JSON file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    """Main page to display the state of the tags."""
    tag_states = load_tag_states()
    return render_template("index.html", tag_states=tag_states)

@app.route('/api/tags')
def get_tags():
    """API endpoint to get the current tag states as JSON."""
    tag_states = load_tag_states()
    return jsonify(tag_states)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
