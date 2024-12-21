from flask import Flask, request, render_template, redirect, url_for, send_file, Response
import sqlite3
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Register the Unicode font for Sanskrit
pdfmetrics.registerFont(TTFont("NotoSansDevanagari", "E:/TEI_encode/fonts/NotoSansDevanagari-VariableFont_wdth,wght.ttf"))

def query_database(query, params=()):
    conn = sqlite3.connect("sanskrit.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

@app.route("/", methods=["GET", "POST"])
def index():
    books = []
    if request.method == "POST":
        book_name = request.form.get("book_name")
        books = query_database("SELECT book_id, title, author FROM Metadata WHERE title LIKE ?", (f"%{book_name}%",))
    return render_template("index.html", books=books)

@app.route("/book/<int:book_id>")
def book(book_id):
    metadata = query_database("SELECT title, author, year FROM Metadata WHERE book_id = ?", (book_id,))
    content = query_database("SELECT chapter, text FROM Content WHERE book_id = ? ORDER BY chapter, content_id", (book_id,))
    metadata = metadata[0] + (book_id,)
    return render_template("book.html", metadata=metadata, content=content)

@app.route("/book/<int:book_id>/download")
def download(book_id):
    content = query_database("SELECT text FROM Content WHERE book_id = ?", (book_id,))
    if not content:
        return "Book not found.", 404
    text_content = content[0][0]
    file_io = BytesIO()
    file_io.write(text_content.encode("utf-8"))
    file_io.seek(0)
    return send_file(file_io, as_attachment=True, download_name=f"book_{book_id}.txt", mimetype="text/plain")

@app.route("/book/<int:book_id>/pdf")
def generate_pdf(book_id):
    metadata = query_database("SELECT title, author, year FROM Metadata WHERE book_id = ?", (book_id,))
    content = query_database("SELECT chapter, text FROM Content WHERE book_id = ?", (book_id,))
    if not metadata or not content:
        return "Book not found.", 404

    # Create a PDF in memory
    pdf_io = BytesIO()
    pdf_canvas = canvas.Canvas(pdf_io)
    pdf_canvas.setFont("NotoSansDevanagari", 12)  # Use the registered font for Sanskrit

    # Write metadata to PDF
    title, author, year = metadata[0]
    pdf_canvas.drawString(50, 800, f"Title: {title}")
    pdf_canvas.drawString(50, 780, f"Author: {author}")
    pdf_canvas.drawString(50, 760, f"Year: {year}")

    # Write content to PDF
    y = 740
    for line in content[0][1].splitlines():
        if y < 50:  # Move to a new page if necessary
            pdf_canvas.showPage()
            pdf_canvas.setFont("NotoSansDevanagari", 12)
            y = 800
        pdf_canvas.drawString(50, y, line)
        y -= 15

    pdf_canvas.save()
    pdf_io.seek(0)

    # Return the PDF to the browser
    return Response(pdf_io, mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
