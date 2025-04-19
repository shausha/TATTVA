from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify
import sqlite3
from io import BytesIO
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
from flask_app import app  # Import your Flask app
import serverless_wsgi

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
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

    # Pass book_id, title, author, year, and content to the template
    return render_template("book.html", 
                           title=title, 
                           author=author, 
                           year=year, 
                           content=content[0][0],  # Only passing the first content entry
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
    # Fetch the content of the book from the Content table
    content = query_database("SELECT text FROM Content WHERE book_id = ?", (book_id,))
    
    if not content:
        return "Book not found.", 404

    # Get the content text (assuming the content is in the first column of the result)
    text_content = content[0][0]

    # Create an in-memory file to send as a response
    file_io = BytesIO()
    file_io.write(text_content.encode("utf-8"))
    file_io.seek(0)

    # Send the file to the user as an attachment with a .txt extension
    return send_file(file_io, as_attachment=True, download_name=f"book_{book_id}.txt", mimetype="text/plain")

@app.route("/search")
def search():
    query = request.args.get("query")
    if query:
        books = query_database("SELECT book_id, title, author FROM Metadata WHERE title LIKE ?", (f"%{query}%",))
        return jsonify({"books": [{"book_id": book[0], "title": book[1], "author": book[2]} for book in books]})
    return jsonify({"books": []})

if __name__ == "__main__":
    app.run(debug=True)
