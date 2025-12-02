
from flask import Flask, request, send_file
import os
from validate_csvs_arcgis_AR import tool_exec

app = Flask(__name__)
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "No file uploaded", 400
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        try:
            html_path = tool_exec(filepath)
            return send_file(html_path, mimetype="text/html")
        except Exception as e:
            return f"Validation failed: {str(e)}", 500
    return """
    <h1>CSV Validator</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".csv" required>
        <button type="submit">Validate</button>
    </form>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
