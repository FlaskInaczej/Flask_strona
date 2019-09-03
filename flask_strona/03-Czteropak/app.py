from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_migrate import Migrate
from flask_mail import Mail
from forms import PostForm, LoginForm, ContactForm

with open("/etc/config.json") as config_file:
    config = json.load(config_file)


app = Flask(__name__)
SECRET_KEY = config.get('SECRET_KEY')
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

app.config.from_object(__name__)
db = SQLAlchemy(app)
whooshee = Whooshee(app)
migrate = Migrate(app, db)
mail = Mail(app)


from routes import *

if __name__ == '__main__':
    app.run()
    
 
 




