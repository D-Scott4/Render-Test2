
from flask import Flask, request, send_file
import os
from werkzeug.utils import secure_filename

from validate_csvs_arcgis_AR import tool_exec

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename.strip() == "":
            return "No file uploaded", 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            html_path = tool_exec(filepath)
            return send_file(html_path, mimetype="text/html")
        except Exception as e:
            return f"Validation failed: {str(e)}", 500

    # Styled upload page
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FI Checker Test</title>
  <style>
    :root{
      --green:#1e7a3a;
      --green-dark:#16612e;
      --bg:#f4f7f5;
      --card:#ffffff;
      --text:#1f2937;
      --muted:#6b7280;
      --border:#e5e7eb;
      --shadow:0 10px 25px rgba(0,0,0,.08);
      --radius:16px;
      --focus:0 0 0 4px rgba(30,122,58,.18);
      --font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
    }

    *{box-sizing:border-box;}
    body{
      margin:0;
      font-family:var(--font);
      color:var(--text);
      background: radial-gradient(900px 500px at 20% -10%, rgba(30,122,58,.16), transparent 60%),
                  radial-gradient(800px 450px at 80% 0%, rgba(30,122,58,.10), transparent 55%),
                  var(--bg);
    }

    /* Top banner */
    .banner{
      position:sticky;
      top:0;
      z-index:10;
      background: linear-gradient(90deg, var(--green), #2aa24d);
      color:#fff;
      box-shadow: 0 6px 18px rgba(0,0,0,.12);
    }
    .banner-inner{
      max-width: 980px;
      margin: 0 auto;
      padding: 16px 20px;
      display:flex;
      align-items:center;
      gap:12px;
    }
    .banner-badge{
      width:36px;
      height:36px;
      border-radius:10px;
      background:rgba(255,255,255,.18);
      display:grid;
      place-items:center;
      font-weight:800;
      letter-spacing:.5px;
    }
    .banner-title{
      font-size: 20px;
      margin:0;
      line-height:1.1;
    }
    .banner-subtitle{
      margin:0;
      font-size: 13px;
      opacity:.9;
    }

    main{
      max-width: 980px;
      margin: 28px auto 50px;
      padding: 0 20px;
    }

    .card{
      background: var(--card);
      border:1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 22px;
    }

    .card h2{
      margin:0 0 6px 0;
      font-size: 18px;
    }

    .card p{
      margin:0 0 18px 0;
      color:var(--muted);
      line-height:1.45;
    }

    .grid{
      display:grid;
      grid-template-columns: 1fr;
      gap:14px;
    }

    .field{
      display:flex;
      flex-direction:column;
      gap:8px;
    }

    .label{
      font-size: 13px;
      color: var(--muted);
      font-weight: 600;
    }

    input[type=file]{
      width:100%;
      padding: 12px 12px;
      border-radius: 12px;
      border:1px solid var(--border);
      background: #fbfbfb;
      outline:none;
    }

    input[type=file]:focus{
      box-shadow: var(--focus);
      border-color: rgba(30,122,58,.6);
    }

    .actions{
      display:flex;
      gap:10px;
      flex-wrap:wrap;
      margin-top: 4px;
    }

    .btn{
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 11px 14px;
      font-weight: 700;
      cursor:pointer;
      transition: transform .06s ease, box-shadow .15s ease, background .15s ease, border-color .15s ease;
      user-select:none;
    }
    .btn:active{transform: translateY(1px);}
    .btn:focus{outline:none; box-shadow: var(--focus);}

    .btn-primary{
      background: var(--green);
      color:#fff;
      box-shadow: 0 8px 16px rgba(30,122,58,.18);
    }
    .btn-primary:hover{background: var(--green-dark);}

    .btn-secondary{
      background: #fff;
      color: var(--text);
      border-color: var(--border);
    }
    .btn-secondary:hover{
      background: #f8fafc;
      border-color: #d1d5db;
    }

    .hint{
      margin-top: 14px;
      padding: 12px 14px;
      border-radius: 12px;
      background: rgba(30,122,58,.06);
      border: 1px dashed rgba(30,122,58,.35);
      color: #0f3d1f;
      font-size: 13px;
    }

    footer{
      margin-top: 18px;
      color: var(--muted);
      font-size: 12px;
      text-align:center;
    }
  </style>
</head>
<body>
  <header class="banner">
    <div class="banner-inner">
      <div class="banner-badge">FI</div>
      <div>
        <h1 class="banner-title">FI Checker Test</h1>
        <p class="banner-subtitle">Upload a CSV and run validation</p>
      </div>
    </div>
  </header>

  <main>
    <section class="card" aria-label="CSV upload">
      <h2>CSV Validator</h2>
      <p>Select a CSV file to validate. The results will open as an HTML report.</p>

      <form method="post" enctype="multipart/form-data" class="grid">
        <label class="field">
          <span class="label">CSV file</span>
          <input type="file" name="file" accept=".csv" required />
        </label>

        <div class="actions">
          <button class="btn btn-primary" type="submit">Validate CSV</button>
          <button class="btn btn-secondary" type="reset">Clear</button>
        </div>
      </form>

      <div class="hint">
        Tip: If your CSV is large, upload may take a moment—please keep this tab open until the report loads.
      </div>
    </section>

    <footer>
      &copy; FI Checker Test
    </footer>
  </main>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
