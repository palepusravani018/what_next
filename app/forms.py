import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from wtforms import (
    StringField, 
    PasswordField, 
    BooleanField, 
    SubmitField, 
    IntegerField, 
    SelectField, 
    SelectMultipleField
)
from wtforms.validators import (
    DataRequired, 
    ValidationError, 
    Email, 
    EqualTo, 
    Length
)

from app import db
from app.models import User

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password")])
    phone = StringField("Phone", validators=[DataRequired()])
    qualification = StringField("qualification",validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data
        ))
        if user is not None:
            raise ValidationError("Please use a different username")
        
    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data
        ))
        if user is not None:
            raise ValidationError("Please use a different email address")

class Question(db.Model):
    __tablename__ = 'question'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=sa.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='questions')

class ProfileForm(FlaskForm):
    phone = StringField("Phone", validators=[DataRequired(), Length(min=10, max=15)])
    avatar = FileField('Update Avatar', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField("Submit")

class GroupForm(FlaskForm):
    id = IntegerField('id')
    name = StringField('name', validators=[DataRequired(), Length(max=50)])
    standard = StringField('standard', validators=[DataRequired(), Length(max=50)])
    prerequisite_groups = SelectMultipleField('Prerequisite Groups', coerce=int)
    submit = SubmitField("Submit")

class CourseForm(FlaskForm):
    id = IntegerField('id')
    type = StringField('type', validators=[DataRequired(), Length(max=50)])
    name = StringField('name', validators=[DataRequired(), Length(max=50)])
    duration = StringField('duration', validators=[DataRequired(), Length(max=50)])
    prerequisite_courses = SelectMultipleField('Prerequisite Courses', coerce=int)
    submit = SubmitField("Submit")
