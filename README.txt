BUSINESS CARD DIGITIZER V2
==========================

What this version does
- Python + OpenCV + Tesseract OCR.
- One photo may contain one card or multiple cards.
- Automatically detects separate card regions where possible.
- OCR and field extraction are independent per detected card.
- Editable Name, Company Name, Job Title, Address, Email, Personal Phone, Company Phone, Website.
- Missing/review fields are highlighted.
- Confirm cards and export one Excel file.
- No login or database. Everything runs locally on your computer.

WINDOWS SETUP (first time only)
1. Install Python 3.11 or 3.12 from python.org and tick "Add Python to PATH".
2. Install Tesseract OCR for Windows and ensure tesseract.exe is in PATH.
3. Open Command Prompt in this folder and run:
      pip install -r requirements.txt
4. Double-click start.bat.
5. Browser opens at http://127.0.0.1:8000

MAC SETUP
1. Install Python 3 and Tesseract (for example via Homebrew: brew install tesseract).
2. In Terminal inside this folder run:
      pip3 install -r requirements.txt
3. Double-click start.command or run: python3 server.py

IMPORTANT
Do not open index.html directly. The HTML talks to the local Python OCR server.
Use http://127.0.0.1:8000, not an editor's static preview or Live Server.
Keep the server's Terminal/Command Prompt window open while using the app.

UPLOAD TROUBLESHOOTING
If an upload says "Unexpected token '<'" or "received HTML", the page is
receiving a web page instead of a response from the Python OCR server.
1. Start start.command (Mac) or start.bat (Windows).
2. Open http://127.0.0.1:8000 and refresh the page.
3. Wait for "Python OCR ready", then choose your photo again.
If startup reports a missing Python module, install requirements.txt using
the same Python that runs server.py. On Mac you can use a local environment:
      python3 -m venv .venv
      .venv/bin/python -m pip install -r requirements.txt
Then start.command will automatically use that environment.

MULTI-CARD PHOTOS
Best results: place cards flat, keep space between them, avoid overlap, and shoot as straight as possible. The app checks grayscale and colour boundaries, corrects perspective, and also checks for text regions outside any cards already found. Each detected card has its own preview, editable fields and confirmation button, and exports as one separate Excel row. If no card can be separated, the whole photo remains available as one review entry.

OCR IMPROVEMENTS
- Separate OCR passes handle scattered text, ordinary rows and textured stock.
- Small titles are read in the name's column, with an extra crop retry if needed.
- Faded coloured names can be read using contrast in the card's colour channels.
- Nearby logo lines are combined and checked against printed website/email domains.
- Inferred company names and corrected abbreviations/honorifics remain marked for review.
- Alternate address readings are deduplicated instead of repeated in the field.
Names, titles and addresses still need a final human check before confirmation.

REGRESSION CHECKS (requires Tesseract and the Python dependencies)
      .venv/bin/python -m unittest discover -s tests -v
      node --test tests/test_client.cjs
On Windows, use python instead of .venv/bin/python after setup.
The photo fixtures include the gold card, the white card and the three-card photo.
