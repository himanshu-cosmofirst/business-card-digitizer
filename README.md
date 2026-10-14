# Business Card Digitizer

Upload one or more photos, review a separate entry for each detected card,
confirm the entries, and download an Excel workbook with one row per card.

The app uses Python, OpenCV, Tesseract OCR, and openpyxl. The hosted entry point
uses Flask and Gunicorn. The app does not maintain a database or upload
archive; OCR uses temporary files during processing. Review highlighted
fields before exporting, especially addresses and faded text.

## Run locally

Install Python and Tesseract, then run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./start.command
```

On Windows, follow [README.txt](README.txt) and run `start.bat`.
Open http://127.0.0.1:8000. Keep the server window open.

## Deploy from GitHub to Render

GitHub stores the source code. GitHub Pages serves static files and cannot run
this Python/Tesseract backend. Render can build the included Dockerfile and
serve both the page and API from the same HTTPS address.

1. Create a **private** GitHub repository named `business-card-digitizer`.
2. Upload the project source files, including `Dockerfile`, `render.yaml`,
   `app.py`, `gunicorn.conf.py`, and both requirements files. The `.gitignore`
   excludes the virtual environment, local card photos, and exported workbooks.
3. Sign in at https://dashboard.render.com and connect the GitHub account with
   access to that private repository.
4. Choose **New → Blueprint**, select the repository, and deploy the service
   defined by `render.yaml`. It requests Render's free web-service plan.
5. Open the service's assigned `https://…onrender.com` URL.
6. Sign in with username `admin` and the generated `APP_PASSWORD` shown in
   that service's Render environment settings. Change the password there if
   desired; keep its value out of GitHub.

The free service can sleep when idle, so its first request may take longer.
For sustained OCR use, choose a suitable paid plan in Render yourself.
The container installs Tesseract from Debian's packages; `/api/health` reports
the actual installed OCR version.

Deployment references: [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages),
[Render Docker](https://render.com/docs/docker),
[Render Blueprints](https://render.com/docs/blueprint-spec),
and [Render free services](https://render.com/docs/free).

## Run the hosted entry point locally

```sh
.venv/bin/python -m pip install -r requirements-hosted.txt
HOST=127.0.0.1 PORT=8001 .venv/bin/gunicorn --config gunicorn.conf.py app:app
```

Open http://127.0.0.1:8001. Set `APP_USERNAME` and `APP_PASSWORD` in the process
environment to enable password protection. Gunicorn listens on the host's
`PORT`; the container runs one worker and limits simultaneous OCR jobs to one.

If Docker is installed:

```sh
docker build -t business-card-digitizer .
docker run --rm -p 8001:8000 business-card-digitizer
```

## Tests

```sh
.venv/bin/python -m pip install -r requirements-hosted.txt
.venv/bin/python -m unittest discover -s tests -v
node --test tests/test_client.cjs
```

Local photo regression tests run when the private fixtures are present under
`tests/fixtures/`. They are skipped in a GitHub checkout without those photos.
The other tests verify extraction rules, JSON responses, password protection,
uploads, and Excel exports.
