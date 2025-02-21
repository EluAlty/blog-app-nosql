# Blog Platform with MongoDB

## Made by Kurmetov Nurlan and Absatar Abzal | SE-2308

## System Architecture
- Flask Backend
- MongoDB Database
- RESTful API endpoints

## Database Structure
1. Users Collection
   - username (string, unique)
   - password (hashed string)
   - role (string)

2. Posts Collection
   - name (string)
   - content (string)
   - author (string)
   - created_at (datetime)
   - likes (array)
   - comments (array)

3. Categories Collection
   - name (string)
   - description (string)

## API Endpoints
- GET /api/posts - Retrieve all posts
- POST /api/posts - Create new post
- PUT /api/posts/<id> - Update post
- DELETE /api/posts/<id> - Delete post

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Set up MongoDB connection
3. Configure environment variables
4. Run application: `python app.py`

## Security Features
- Bcrypt password hashing
- Session-based authentication
- Role-based access control







