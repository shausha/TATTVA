from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from io import BytesIO
from werkzeug.utils import secure_filename
import os
import time

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Ensure uploads directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# MongoDB connection with retry logic
uri = "mongodb+srv://ushajawahar23:ushausha@tattva.n09jmdw.mongodb.net/?retryWrites=true&w=majority&appName=Tattva"

# Create a new client with explicit TLS settings
client = MongoClient(
    uri,
    server_api=ServerApi('1'),
    tls=True,
    tlsAllowInvalidCertificates=True,  # For testing only
    connectTimeoutMS=30000,
    serverSelectionTimeoutMS=30000
)

# Add connection retry logic
max_retries = 3
retry_count = 0
connected = False

while retry_count < max_retries and not connected:
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        connected = True
    except Exception as e:
        retry_count += 1
        print(f"Connection attempt {retry_count} failed: {e}")
        if retry_count < max_retries:
            print(f"Retrying in 5 seconds...")
            time.sleep(5)
        else:
            print(f"Failed to connect after {max_retries} attempts")

# Set your database
db = client["tattva"]

@app.route("/", methods=["GET", "POST"])
def index():
    books = []
    try:
        if request.method == "POST":
            book_name = request.form.get("book_name")
            if book_name:
                # MongoDB query with case-insensitive search
                books = list(db.metadata.find({"title": {"$regex": book_name, "$options": "i"}}, 
                                          {"_id": 1, "title": 1, "author": 1}))
                # Transform MongoDB _id to book_id for compatibility
                for book in books:
                    book["book_id"] = str(book["_id"])
    except Exception as e:
        print(f"Database error in index route: {e}")
    return render_template("index.html", books=books)

@app.route("/book/<book_id>")
def book(book_id):
    try:
        # Convert string ID to ObjectId for MongoDB
        book_object_id = ObjectId(book_id)
        
        # Fetch metadata (title, author, year)
        metadata = db.metadata.find_one({"_id": book_object_id})
        
        if not metadata:
            return "Book metadata not found.", 404
            
        # Fetch content (full text of the book)
        content = db.content.find_one({"book_id": book_object_id})
        
        if not content:
            return "Book content not found.", 404

        # Pass book_id, title, author, year, and content to the template
        return render_template("book.html", 
                            title=metadata.get("title", "Unknown Title"), 
                            author=metadata.get("author", "Unknown Author"), 
                            year=metadata.get("year", "Unknown Year"), 
                            content=content.get("text", ""),
                            book_id=book_id)
    except Exception as e:
        print(f"Error in book route: {e}")
        return f"Error: {str(e)}", 500

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        try:
            title = request.form.get("title", "")
            author = request.form.get("author", "")
            year = request.form.get("year", "")
            file = request.files.get("file")
            
            if not title or not author or not file:
                return "Missing required fields", 400
                
            # Ensure the file is allowed (only .txt files)
            if file and file.filename.endswith(".txt"):
                try:
                    # Read the content from the uploaded file
                    file_content = file.read().decode("utf-8")
                    
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
                        "text": file_content
                    })

                    # Redirect to the index page after successful upload
                    return redirect(url_for("index"))
                except Exception as e:
                    print(f"Error processing file: {e}")
                    return f"Error processing file: {str(e)}", 500
            else:
                return "Only .txt files are allowed", 400
        except Exception as e:
            print(f"Error in upload route: {e}")
            return f"Error: {str(e)}", 500
            
    return render_template("upload.html")

@app.route("/book/<book_id>/download")
def download(book_id):
    try:
        # Fetch the content of the book from the Content collection
        content = db.content.find_one({"book_id": ObjectId(book_id)})
        
        if not content:
            return "Book content not found.", 404

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
        print(f"Error in download route: {e}")
        return f"Error: {str(e)}", 500

@app.route("/search")
def search():
    try:
        query = request.args.get("query", "")
        if query:
            # MongoDB query with case-insensitive search
            books = list(db.metadata.find({"title": {"$regex": query, "$options": "i"}}, 
                                        {"_id": 1, "title": 1, "author": 1}))
            # Transform MongoDB documents for JSON response
            book_list = []
            for book in books:
                book_list.append({
                    "book_id": str(book["_id"]),
                    "title": book.get("title", "Unknown Title"),
                    "author": book.get("author", "Unknown Author")
                })
            return jsonify({"books": book_list})
        return jsonify({"books": []})
    except Exception as e:
        print(f"Error in search route: {e}")
        return jsonify({"error": str(e), "books": []}), 500

if __name__ == "__main__":
    app.run(debug=True)