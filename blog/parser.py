import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import credentials

client = MongoClient(credentials.uri, server_api=ServerApi('1'))
db = client.Cluster0
product = db.product

def parse_medium_rss(username):
    """Parse Medium RSS feed for a specific user"""
    url = f'https://medium.com/feed/@{username}'
    feed = feedparser.parse(url)
    
    posts = []
    for entry in feed.entries:
        
        soup = BeautifulSoup(entry.content[0].value, 'html.parser')
        content = soup.get_text()
        
        
        img = soup.find('img')
        image_url = img['src'] if img else None
        
        post = {
            'name': entry.title,
            'content': content,
            'author': username,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'image_url': image_url,
            'likes': [],
            'comments': [],
            'source': 'medium'
        }
        posts.append(post)
    return posts

def parse_dev_to():
    """Parse dev.to articles"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = 'https://dev.to/api/articles'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  
        articles = response.json()
        
        posts = []
        for article in articles:
            post = {
                'name': article['title'],
                'content': article.get('description', ''),
                'author': article['user']['name'],
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'image_url': article.get('cover_image', ''),
                'likes': [],
                'comments': [],
                'source': 'dev.to'
            }
            posts.append(post)
        return posts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching dev.to articles: {e}")
        return []

def parse_additional_source():
    """Parse articles from additional source"""
    try:
        response = requests.get(
            'https://api.newsapi.org/v2/everything',
            headers={'Authorization': 'your_api_key'},
            params={'q': 'technology', 'pageSize': 10}
        )
        articles = response.json()['articles']
        
        posts = []
        for article in articles:
            post = {
                'name': article['title'],
                'content': article['description'],
                'author': article['author'] or 'Unknown',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'image_url': article['urlToImage'],
                'likes': [],
                'comments': [],
                'source': 'newsapi'
            }
            posts.append(post)
        return posts
    except Exception as e:
        logger.error(f"Error fetching from NewsAPI: {e}")
        return []

def import_posts():
    """Import posts from all sources"""
    try:
        
        medium_posts = parse_medium_rss('medium')
        for post in medium_posts:
            
            if not product.find_one({'name': post['name']}):
                product.insert_one(post)
        
      
        dev_posts = parse_dev_to()
        for post in dev_posts:
            if not product.find_one({'name': post['name']}):
                product.insert_one(post)
                
       
        additional_posts = parse_additional_source()
        for post in additional_posts:
            if not product.find_one({'name': post['name']}):
                product.insert_one(post)
                
        print("Posts imported successfully!")
    except Exception as e:
        print(f"Error importing posts: {e}")

def setup_indexes():
    """Setup MongoDB indexes for optimization"""
   
    product.create_index([('name', 'text'), ('content', 'text')])
    
   
    product.create_index('author')
    
   
    product.create_index([('likes', 1), ('comments', 1)])

if __name__ == "__main__":
    import_posts() 