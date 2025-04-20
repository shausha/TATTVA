from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from io import BytesIO
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection
uri = "mongodb+srv://ushajawahar23:ushausha@tattva.n09jmdw.mongodb.net/?retryWrites=true&w=majority&appName=Tattva"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Test the connection (you can remove this part in production)
try:
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Connection error: {e}")

# Set your database
db = client["tattva"]

@app.route("/", methods=["GET", "POST"])
def index():
    books = []
    if request.method == "POST":
        book_name = request.form.get("book_name")
        # MongoDB query with case-insensitive search
        books = list(db.metadata.find({"title": {"$regex": book_name, "$options": "i"}}, 
                                    {"_id": 1, "title": 1, "author": 1}))
        # Transform MongoDB _id to book_id for compatibility
        for book in books:
            book["book_id"] = str(book["_id"])
    return render_template("index.html", books=books)

@app.route("/book/<book_id>")
def book(book_id):
    # Fetch metadata (title, author, year)
    try:
        # Convert string ID to ObjectId for MongoDB
        metadata = db.metadata.find_one({"_id": ObjectId(book_id)})
        # Fetch content (full text of the book)
        content = db.content.find_one({"book_id": ObjectId(book_id)})

        if not metadata or not content:
            return "Book not found.", 404

        # Pass book_id, title, author, year, and content to the template
        return render_template("book.html", 
                            title=metadata.get("title"), 
                            author=metadata.get("author"), 
                            year=metadata.get("year"), 
                            content=content.get("text"),  # Get the text content
                            book_id=book_id)
    except Exception as e:
        return f"Error: {str(e)}", 500

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

            # Insert book metadata into MongoDB
            metadata_result = db.metadata.insert_one({
                "title": title,
                "author": author,
                "year": year
            })
            
            # Get the ID of the inserted metadata document
            book_id = metadata_result.inserted_id

            # Insert the entire content into the Content collection
            db.content.insert_one({
                "book_id": book_id,
                "text": file_content  # Insert the full text content of the file
            })

            # Redirect to the index page after successful upload
            return redirect(url_for("index"))  # Redirect to the home page

    return render_template("upload.html")
@app.route("/book/<book_id>/download")
def download(book_id):
    try:
        # Fetch the content of the book from the Content collection
        content = db.content.find_one({"book_id": ObjectId(book_id)})
        
        if not content:
            return "Book not found.", 404

        # Get the content text
        text_content = content.get("text", "")

        # Create an in-memory file to send as a response
        file_io = BytesIO()
        file_io.write(text_content.encode("utf-8"))
        file_io.seek(0)

        # Get the book title for the filename if available
        metadata = db.metadata.find_one({"_id": ObjectId(book_id)})
        filename = f"{metadata.get('title', f'book_{book_id}')}.txt" if metadata else f"book_{book_id}.txt"

        # Send the file to the user as an attachment with a .txt extension
        return send_file(file_io, as_attachment=True, download_name=filename, mimetype="text/plain")
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/search")
def search():
    query = request.args.get("query")
    if query:
        # MongoDB query with case-insensitive search
        books = list(db.metadata.find({"title": {"$regex": query, "$options": "i"}}, 
                                     {"_id": 1, "title": 1, "author": 1}))
        # Transform MongoDB documents for JSON response
        book_list = []
        for book in books:
            book_list.append({
                "book_id": str(book["_id"]),
                "title": book["title"],
                "author": book["author"]
            })
        return jsonify({"books": book_list})
    return jsonify({"books": []})

if __name__ == "__main__":
    app.run(debug=True)
