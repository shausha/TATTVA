# Sanskrit Digital Library

## Deployment Guide for Netlify

### Prerequisites
1. Create a MongoDB Atlas account and set up a cluster
2. Create a Netlify account
3. Install Netlify CLI (optional for local testing)

### MongoDB Atlas Setup
1. Create a new cluster in MongoDB Atlas
2. Create a database user with read/write permissions
3. Get your connection string from MongoDB Atlas

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

### Important: Environment Variables
For security, you must set these environment variables in the Netlify dashboard:
1. Go to Site settings > Build & deploy > Environment
2. Add the following variables:
   - MONGODB_URI: Your MongoDB connection string (with your actual username and password)
   - MONGODB_DB: tattva

### Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Create a `.env` file with your MongoDB credentials (do not commit this to Git)
3. Run the Flask application: `python app.py`

### Troubleshooting Netlify Deployment
If you encounter a "Page not found" error:
1. Check the Function logs in your Netlify dashboard
2. Verify your MongoDB connection string is correctly set in Environment variables
3. Make sure all redirects are properly configured in netlify.toml

### Notes
- Ensure all Python dependencies are listed in `requirements.txt`
- The application uses Flask and MongoDB for backend operations
- Files are stored as text in the MongoDB database