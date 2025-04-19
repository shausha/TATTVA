# Sanskrit Digital Library

## Deployment Guide

### Prerequisites
1. Create a MongoDB Atlas account and set up a free cluster
2. Create a Netlify account
3. Install Netlify CLI (optional for local testing)

### MongoDB Atlas Setup
1. Create a new cluster in MongoDB Atlas
2. Create a database user with read/write permissions
3. Get your connection string from MongoDB Atlas
4. Replace the placeholder MongoDB URI in `netlify.toml` with your actual connection string

### Netlify Deployment Steps
1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)
2. Log in to Netlify and create a new site from Git
3. Connect your repository
4. Configure the build settings:
   - Build command: `pip install -r requirements.txt`
   - Publish directory: `.`
5. Add environment variables in Netlify:
   - MONGODB_URI: Your MongoDB Atlas connection string
   - MONGODB_DB: tattva

### Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in a `.env` file
3. Run the Flask application: `python app.py`

### Notes
- Ensure all Python dependencies are listed in `requirements.txt`
- The application uses Flask and MongoDB for backend operations
- Files are stored as text in the MongoDB database