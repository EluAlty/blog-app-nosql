from flask import Flask, render_template, request, url_for, redirect, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import bcrypt
import credentials
import os
from werkzeug.utils import secure_filename
from datetime import datetime


client = MongoClient(credentials.uri, server_api=ServerApi('1'))


db = client.Cluster0
product = db.product
user_log = db.login
categories = db.categories

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testing'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

ADMIN_PASSWORD = "admin"  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=("GET", "POST"))
def index():
    if request.method == 'POST':
        render_template('posts.html')
        print("test")

    all_posts = product.find()

    return render_template('index.html', product=all_posts)


@app.route('/admin_auth', methods=['POST'])
def admin_auth():
    if request.method == 'POST':
        admin_password = request.form.get('admin_password')
        if admin_password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin'))
        return redirect(url_for('admin'))


@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    is_admin = session.get('is_admin', False)
    if is_admin:
      
        posts = list(product.find())
    else:
        
        posts = list(product.find({'author': session['username']}))
    
    return render_template('admin.html', posts=posts, is_admin=is_admin)


@app.route("/posts/<name>", methods=["GET"])
def post(name):
    post = product.find_one({"name": name})
    if post:
        return render_template('posts.html', post=post)
    return redirect(url_for('index'))


@app.route('/<id>/delete/', methods=("GET", "POST"))
def delete(id):
    post = product.find_one({'_id': ObjectId(id)})
    if post and (session.get('is_admin', False) or post['author'] == session['username']):
        product.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))


@app.route('/<id>/edit/', methods=['GET', 'POST'])
def edit(id):
    post = product.find_one({'_id': ObjectId(id)})
    if not post or (not session.get('is_admin', False) and post['author'] != session['username']):
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
      
        product.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': request.form.get('name'),
                'content': request.form.get('content'),
                'image_url': request.form.get('image_url')
            }}
        )
        return redirect(url_for('admin'))
    
    return render_template('edit.html', post=post)


@app.route('/process', methods=['POST'])
def process():
    find = request.form.get('search_query')
    if find:
        results = product.find({'name': {'$regex': find, '$options': 'i'}})
        search_results = list(results)
        return render_template('index.html', product=search_results)
    return redirect(url_for('index'))


def create_hashed_password(password):
    encoded = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(encoded, salt)
    return hashed


@app.route('/login', methods=("GET", "POST"))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = user_log.find_one({'username': username})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)
    
    return render_template('login.html')


@app.route('/signup', methods=("GET", "POST"))
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = user_log.find_one({'username': username})
        
        if existing_user:
            error = "Username already exists"
            return render_template('signup.html', error=error)
            
        if len(password) < 7:
            error = "Password must be at least 7 characters long"
            return render_template('signup.html', error=error)
            
        hashed = create_hashed_password(password)
        user_log.insert_one({'username': username, 'password': hashed})
        session['username'] = username
        return redirect(url_for('index'))
        
    return render_template('signup.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/like/<post_id>', methods=['POST'])
def like_post(post_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    post = product.find_one({'_id': ObjectId(post_id)})
    if not post:
        return redirect(url_for('index'))
    
    likes = post.get('likes', [])
    if username in likes:
        product.update_one(
            {'_id': ObjectId(post_id)},
            {'$pull': {'likes': username}}
        )
    else:
        product.update_one(
            {'_id': ObjectId(post_id)},
            {'$addToSet': {'likes': username}}
        )
    
    return redirect(request.referrer or url_for('index'))


@app.route('/post/<name>/comment', methods=['POST'])
def add_comment(name):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    content = request.form.get('comment')
    if not content:
        return redirect(url_for('post', name=name))
    
    comment = {
        'author': session['username'],
        'content': content,
        'created_at': datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    
    product.update_one(
        {'name': name},
        {'$push': {'comments': comment}}
    )
    
    return redirect(url_for('post', name=name))


if __name__ == '__main__':
    app.run()