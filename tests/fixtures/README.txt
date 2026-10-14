These local regression photos come from the user's supplied business cards:

gold-card.jpg: IMG_1948 1.jpg, Ambrish Deshpande / Meta Infotech / COO.
white-card.jpg: IMG_1947 1.jpg, Pavan Kumar Verma / Embee.
three-cards.jpg: IMG_1985 1.jpg, the two gold cards and one white card.

Fixtures retain the whole photo, scaled to at most 3200 pixels on the longest
side and saved at JPEG quality 94. Tests also checked the original-resolution
files in Downloads while implementing the fix.

test_ocr.py verifies names, companies, titles, contact separation, independent
Excel rows, and continuation of text detection when only one rectangle is found.
