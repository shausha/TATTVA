from flask import Flask, request, render_template, redirect, url_for
import sqlite3
from lxml import etree
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def query_database(query, params=()):
    conn = sqlite3.connect("sanskrit.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.commit()
    conn.close()
    return results

@app.route("/", methods=["GET", "POST"])
def index():
    books = []
    if request.method == "POST":
        book_name = request.form.get("book_name")
        books = query_database("SELECT book_id, title, author FROM Metadata WHERE title LIKE ?", (f"%{book_name}%",))
    return render_template("index.html", books=books)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        year = request.form.get("year")
        text_file = request.files.get("text_file")

        # Validate the uploaded file
        if not (text_file and allowed_file(text_file.filename)):
            return "Invalid text file."

        # Process the text file for TEI encoding
        text_content = text_file.read().decode("utf-8")
        tei_content = create_tei(text_content)

        # Insert into the database
        query_database(
            "INSERT INTO Metadata (title, author, year, text) VALUES (?, ?, ?, ?)",
            (title, author, year, tei_content)
        )
        return redirect(url_for("index"))
    return render_template("upload.html")

from lxml import etree

def create_tei(text_content):
    """Create TEI encoding for the given Sanskrit text with minimal structure."""
    
    # Create the root TEI element
    root = etree.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    
    # TEI Header
    tei_header = etree.SubElement(root, "teiHeader")
    file_desc = etree.SubElement(tei_header, "fileDesc")
    title_stmt = etree.SubElement(file_desc, "titleStmt")
    etree.SubElement(title_stmt, "title").text = "Uploaded Sanskrit Manuscript"
    etree.SubElement(title_stmt, "author").text = "Unknown Author"
    publication_stmt = etree.SubElement(file_desc, "publicationStmt")
    etree.SubElement(publication_stmt, "publisher").text = "Unknown Publisher"
    
    # Text section starts here
    text_elem = etree.SubElement(root, "text")
    body = etree.SubElement(text_elem, "body")
    
    paragraphs = text_content.splitlines()
    for line in paragraphs:
        line = line.strip()
        if line:
            p = etree.SubElement(body, "p")
            p.text = line
    
    return etree.tostring(root, encoding="unicode")


@app.route("/book/<int:book_id>")
def book(book_id):
    # Fetch book metadata
    metadata = query_database("SELECT title, author, year, text FROM Metadata WHERE book_id = ?", (book_id,))
    if not metadata:
        return "Book not found.", 404

    # Extract metadata fields
    title, author, year, text = metadata[0]

    # Pass these fields to the template
    return render_template("book.html", title=title, author=author, year=year, text=text, book_id=book_id)


if __name__ == "__main__":
    app.run(debug=True)
