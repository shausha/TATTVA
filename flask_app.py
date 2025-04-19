from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify
from pymongo import MongoClient
from bson import ObjectId
from io import BytesIO
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# MongoDB connection using environment variables
def get_database_connection():
    mongo_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://ushajawahar23:ushausha@tattva.n09jmdw.mongodb.net/')
    client = MongoClient(mongo_uri)
    database_name = os.environ.get('MONGODB_DB', 'tattva')
    return client[database_name]

# Get database collections
db = get_database_connection()
metadata_collection = db['metadata']
content_collection = db['content']

@app.route("/", methods=["GET", "POST"])
def index():
    books = []
    if request.method == "POST":
        book_name = request.form.get("book_name")
        books = list(metadata_collection.find({"title": {"$regex": book_name, "$options": "i"}}))
        # Convert ObjectId to string for JSON serialization
        for book in books:
            book['_id'] = str(book['_id'])
    return render_template("index.html", books=books)

@app.route("/book/<book_id>")
def book(book_id):
    # Fetch metadata (title, author, year)
    metadata = metadata_collection.find_one({"_id": ObjectId(book_id)})
    # Fetch content (full text of the book)
    content = content_collection.find_one({"book_id": ObjectId(book_id)})

    if not metadata or not content:
        return "Book not found.", 404

    # Pass book_id, title, author, year, and content to the template
    return render_template("book.html", 
                           title=metadata['title'], 
                           author=metadata['author'], 
                           year=metadata['year'], 
                           content=content['text'],
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
            metadata_result = metadata_collection.insert_one({
                "title": title,
                "author": author,
                "year": year
            })

            # Insert the entire content into the Content collection
            content_collection.insert_one({
                "book_id": metadata_result.inserted_id,
                "text": file_content
            })

            # Redirect to the index page after successful upload
            return redirect(url_for("index"))  # Redirect to the home page

    return render_template("upload.html")

@app.route("/book/<book_id>/download")
def download(book_id):
    # Fetch the content of the book from the Content collection
    content = content_collection.find_one({"book_id": ObjectId(book_id)})
    
    if not content:
        return "Book not found.", 404

    # Get the content text
    text_content = content['text']

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
        books = list(metadata_collection.find({"title": {"$regex": query, "$options": "i"}}))
        # Convert ObjectId to string for JSON serialization
        return jsonify({"books": [{
            "book_id": str(book['_id']), 
            "title": book['title'], 
            "author": book['author']
        } for book in books]})
    return jsonify({"books": []})

if __name__ == "__main__":
    app.run(debug=True)