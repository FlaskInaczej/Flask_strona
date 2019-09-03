from flask_wtf import FlaskForm, RecaptchaField
from wtforms import PasswordField, SubmitField, BooleanField, StringField, TextAreaField
from wtforms.validators import  DataRequired, Email

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
