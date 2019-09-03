from datetime import datetime
from app import db, whooshee

@whooshee.register_model('title', 'body')
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.Text)
    slug = db.Column(db.String(100), unique=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    published = db.Column(db.Boolean)
    
    def __init__(self, title, body, slug=None, published=True, date_posted=None):
        self.title = title
        self.body = body
        self.slug = slug
        self.published = published
        self.date_posted = datetime.utcnow()

    def __repr__(self):
        return f"Entry('{self.title}', '{self.slug}','{self.date_posted}', '{self.published}')"
