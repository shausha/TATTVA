from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify
import sqlite3
from io import BytesIO
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

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
    # Fetch metadata (title, author, year)
    metadata = query_database("SELECT title, author, year FROM Metadata WHERE book_id = ?", (book_id,))
    # Fetch content (full text of the book)
    content = query_database("SELECT text FROM Content WHERE book_id = ?", (book_id,))

    if not metadata or not content:
        return "Book not found.", 404

    # Metadata is a list, so we need to unpack it
    title, author, year = metadata[0]
    
    # Get the format parameter (default to 'plain')
    format_type = request.args.get('format', 'plain')
    
    # Get the raw content
    raw_content = content[0][0]
    
    if format_type == 'tei':
        # Convert to TEI format
        display_content = convert_to_tei(title, author, year, raw_content)
        content_type = 'tei'
    elif format_type == 'entities':
        # Identify and mark entities
        display_content = identify_entities(raw_content)
        content_type = 'entities'
    else:
        # Plain text
        display_content = raw_content
        content_type = 'plain'

    # Pass book_id, title, author, year, and content to the template
    return render_template("book.html", 
                           title=title, 
                           author=author, 
                           year=year, 
                           content=display_content,
                           content_type=content_type,
                           book_id=book_id)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        year = request.form["year"]
        file = request.files["file"]
        
        # Ensure the file is allowed (only .txt files)
        if file and file.filename.endswith(".txt"):
            # Read the content from the uploaded file
            file_content = file.read().decode("utf-8")  # Decode the file content as UTF-8

            # Insert book metadata into the database
            conn = sqlite3.connect("sanskrit.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Metadata (title, author, year) VALUES (?, ?, ?)",
                (title, author, year)
            )
            book_id = cursor.lastrowid  # Get the ID of the inserted book
            conn.commit()

            # Insert the entire content into the Content table
            cursor.execute(
                "INSERT INTO Content (book_id, text) VALUES (?, ?)",
                (book_id, file_content)  # Insert the full text content of the file
            )
            conn.commit()

            conn.close()

            # Redirect to the index page after successful upload
            return redirect(url_for("index"))  # Redirect to the home page

    return render_template("upload.html")
@app.route("/book/<int:book_id>/download")
def download(book_id):
    # Fetch metadata and content
    metadata = query_database("SELECT title, author, year FROM Metadata WHERE book_id = ?", (book_id,))
    content = query_database("SELECT text FROM Content WHERE book_id = ?", (book_id,))
    
    if not metadata or not content:
        return "Book not found.", 404
    
    # Get format parameter (default to txt)
    format_type = request.args.get('format', 'txt')
    
    title, author, year = metadata[0]
    text_content = content[0][0]
    
    # Create an in-memory file
    file_io = BytesIO()
    
    if format_type == 'tei':
        # Convert to TEI XML
        tei_content = convert_to_tei(title, author, year, text_content)
        file_io.write(tei_content.encode("utf-8"))
        mimetype = "application/xml"
        extension = "xml"
    else:
        # Plain text
        file_io.write(text_content.encode("utf-8"))
        mimetype = "text/plain"
        extension = "txt"
    
    file_io.seek(0)
    
    # Send the file with appropriate name and mimetype
    return send_file(
        file_io, 
        as_attachment=True, 
        download_name=f"{secure_filename(title)}.{extension}", 
        mimetype=mimetype
    )
@app.route("/search")
def search():
    query = request.args.get("query")
    if query:
        books = query_database("SELECT book_id, title, author FROM Metadata WHERE title LIKE ?", (f"%{query}%",))
        return jsonify({"books": [{"book_id": book[0], "title": book[1], "author": book[2]} for book in books]})
    return jsonify({"books": []})

if __name__ == "__main__":
    app.run(debug=True)
