ffrom datetime import datetime
from functools import wraps
from urllib.parse import urljoin
from flask import Flask, render_template, Response,  url_for, flash, redirect, session, request
from werkzeug.contrib.atom import AtomFeed
from slugify import slugify
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import PasswordField, SubmitField, BooleanField, StringField, TextAreaField
from wtforms.validators import  DataRequired, Email
from flask_migrate import Migrate
from flask_mail import Mail, Message
import os
import json
import bleach

with open('/etc/config.json') as config_file:
    config = json.load(config_file)



SECRET_KEY= config.get('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = config.get('DATABASE')
ADMIN_PASSWORD =  config.get('ADMIN_PASSWORD')
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SLL = True
MAIL_USERNAME = config.get('MAIL_USERNAME')
MAIL_PASSWORD = config.get('MAIL_PASSWORD')
RECAPTCHA_PUBLIC_KEY = config.get('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = config.get('RECAPTCHA_PRIVATE_KEY')

app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)
whooshee = Whooshee(app)
migrate = Migrate(app, db)
mail = Mail(app)



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
 
 
class PostForm(FlaskForm):
    title = StringField('Tytuł', validators=[DataRequired()])
    body = TextAreaField('Treść', validators=[DataRequired()])
    status = BooleanField('Opublikowany')
    submit = SubmitField('Zapisz')    

class LoginForm(FlaskForm):
    password = StringField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zapisz')
    recaptcha = RecaptchaField()

class ContactForm(FlaskForm):
    name = StringField('Imię i Nazwisko', validators=[DataRequired('Proszę podać  imię i nazwisko')])
    email = StringField('Email', validators=[Email('Adres email jest niepoprawny')])
    message  = TextAreaField('Treść wiadomości', validators=[DataRequired('Wiadomość bez treści?')])
    submit = SubmitField('Wyślij')
    recaptcha = RecaptchaField()

def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return f(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        if password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session.permanent = True
            flash('Zalogowano pomyślnie', 'success')
            return redirect(url_for('home'))
    return render_template('login.html', title='Login', form=form)

@app.route('/logout/', methods=['GET', 'POST'])
def logout():
        session.clear()
        flash('Wylogowano pomyślnie', 'success')
        return redirect(url_for('home'))
    

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message('Mail wysłany ze strony', sender=app.config['MAIL_USERNAME'], recipients = ['odbiorca@poczta.com'])
        msg.body = """
        Od: %s <%s>
        %s
        """ %(form.name.data, form.email.data, form.message.data)
        mail.send(msg)
        flash('Wiadomość wysłano', 'success')
    return render_template('contact.html', form=form)

@app.route('/create/', methods=['GET', 'POST'])
@login_required
def nowy_post():
    form = PostForm()
    if form.validate_on_submit():
        cleaned_data = bleach.clean(
            form.body.data, 
            tags=bleach.sanitizer.ALLOWED_TAGS + ['h1', 'h2', 'h3', 'h4', 'h5',
            'h6', 'iframe', 'img', 'p', 'pre', 'src', 'u', 'sup', 'sub', 'strike', 'br'],
            attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES)
        post = Entry(
            title=form.title.data, 
            body=cleaned_data,
            published=form.status.data,
         )
        db.session.add(post)
        db.session.commit()

        slug = slugify(str(post.id) + '-' + post.title)
        post.slug = slug
        db.session.commit()

        flash('Post został dodany', 'success')
        return redirect(url_for('article', slug=slug))
    return render_template('create.html', form=form)

@app.route('/<slug>/')
def article(slug):
    post = Entry.query.filter_by(slug=slug).first_or_404()    
    return render_template('post.html', post=post, slug=post.slug)

@app.route('/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit(slug):
    post = Entry.query.filter_by(slug=slug).first_or_404()
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.published = form.status.data
        db.session.commit()
        flash('Wpis został zaaktualizowany!', 'success')
        return redirect(url_for('article', slug=post.slug))
    elif request.method == 'GET':
        form.title.data = post.title
        form.body.data = post.body
        form.status.data = post.published
    return render_template('create.html', title='Edytuj Wpis', 
                           form=form, legend='Edytuj Wpis') 
POSTS_PER_PAGE = 10

@app.route('/')
def home():
    page = int(request.values.get('page', '1'))
    search_query = request.args.get('q')
    if search_query:
        posts = Entry.query.whooshee_search(search_query).filter_by(published=True).order_by(Entry.date_posted.desc())\
            .paginate(page, POSTS_PER_PAGE, False)
    else:
        posts = Entry.query.filter_by(published=True).order_by(Entry.date_posted.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('home.html', posts=posts)

@app.route('/drafts/')
@login_required
def drafts():
    page = int(request.values.get('page', '1'))
    posts = Entry.query.filter_by(published=False).order_by(Entry.date_posted.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('home.html', posts=posts)

@app.route('/latest.atom')
def feeds():
    feed = AtomFeed('Ostatnimi czasy dodane', 
                    feed_url=request.url,
                    url=request.url_root)
    posts = Entry.query.filter_by(published=True).order_by(Entry.date_posted.desc())
    
    for post in posts:
        feed.add(post.title, post.body, content_type='html', author="Flask Inaczej", url=get_abs_url(post.slug), updated=post.date_posted, published=post.date_posted)
    return feed.get_response()

@app.route('/rss')
def atom():
    return render_template('rss.html')

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404 

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run()


