import os
from flask_login import UserMixin
from app import db
from datetime import timedelta
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
import pydenticon, hashlib, base64
from app import login
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash


# User table
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    phone: so.Mapped[str] = so.mapped_column(sa.String(15), index=True, unique=True)
    qualification: so.Mapped[str] = so.mapped_column(sa.String(64))
    is_admin: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    avatar: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def gen_avatar(self, size=36, write_png=True):
        foreground = [ 
            "rgb(45,79,255)",
            "rgb(254,180,44)",
            "rgb(226,121,234)",
            "rgb(30,179,253)",
            "rgb(232,77,65)",
            "rgb(49,203,115)",
            "rgb(141,69,170)"
        ]
        background = "rgb(256,256,256)"

        digest = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        basedir = os.path.abspath(os.path.dirname(__file__))
        pngloc = os.path.join(basedir, 'usercontent', 'identicon', str(digest) + '.png')
        icongen = pydenticon.Generator(5, 5, digest=hashlib.md5, foreground=foreground, background=background)
        pngicon = icongen.generate(self.email, size, size, padding=(8, 8, 8, 8), inverted=False, output_format="png")
        
        if write_png:
            if not os.path.exists(os.path.join(basedir, 'usercontent', 'identicon')):
                os.makedirs(os.path.join(basedir, 'usercontent', 'identicon'))  # Ensure directory exists
            with open(pngloc, "wb") as pngfile:
                pngfile.write(pngicon)
        else:
            return str(base64.b64encode(pngicon))[2:-1]
        
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Group(db.Model):
    __tablename__ = 'groups'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)  # Primary key
    name: so.Mapped[str] = so.mapped_column(sa.String(100))  
    standard: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50))
    prerequisite_groups = db.relationship(
        'GroupPrerequisite',
        primaryjoin='Group.id == GroupPrerequisite.group_id',
        back_populates='group'
    )

class GroupPrerequisite(db.Model):
    __tablename__ = 'group_prerequisites'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    prerequisite_group_id = db.Column(db.Integer, db.ForeignKey(Group.id), nullable=False)
    group = db.relationship('Group', foreign_keys=[group_id], backref='group_prerequisites')
    prerequisite_group = db.relationship('Group', foreign_keys=[prerequisite_group_id])

# class Course(db.Model):
#     __tablename__ = 'courses'
    
#     id: so.Mapped[int] = so.mapped_column(primary_key=True)  # Primary key
#     name: so.Mapped[str] = so.mapped_column(sa.String(100))  
#     type: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50))
#     duration: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50))
#     prerequisite_courses = db.relationship(
#         'CoursePrerequisite',
#         primaryjoin='Course.id == CoursePrerequisite.course_id',
#         back_populates='course'
#     )
# class CoursePrerequisite(db.Model):
#     __tablename__ = 'course_prerequisites'
#     id = db.Column(db.Integer, primary_key=True)
#     course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
#     prerequisite_course_id = db.Column(db.Integer, db.ForeignKey(Course.id), nullable=False)
#     course = db.relationship('Course', foreign_keys=[course_id], backref='course_prerequisites')
#     prerequisite_course = db.relationship('Course', foreign_keys=[prerequisite_course_id])

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))