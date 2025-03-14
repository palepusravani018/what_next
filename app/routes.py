import os
from urllib.parse import urlsplit
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
import sqlalchemy as sa
from app import db, app
from app.models import User, Group, GroupPrerequisite, Course, CoursePrerequisite, Subject
from app.forms import LoginForm, RegistrationForm, ProfileForm, GroupForm,FlaskForm,CourseForm, SubjectForm


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template("index.html", title="Home")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        
        login_user(user, remember=form.remember_me.data)
        
        # Handle the 'next' argument in the request
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for("index")
        
        return redirect(next_page)
    
    return render_template("login.html", title="Sign In", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, phone=form.phone.data, qualification=form.qualification.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    return render_template('user.html', user=user)

@app.route("/user/<username>/edit", methods=["GET", "POST"])
@login_required
def profile(username):
    user = db.session.scalar(sa.select(User).where(User.username == username))

    if user != current_user and not current_user.is_admin:
        flash('You do not have permission to edit this profile.', 'danger')
        return redirect(url_for('index'))

    form = ProfileForm()

    if request.method == "GET":
        form.phone.data = user.phone

    if form.validate_on_submit():
        # Update phone number
        user.phone = form.phone.data

        # Handle avatar file upload
        if form.avatar.data:
            avatar = form.avatar.data
            if avatar:
                filename = secure_filename(avatar.filename)
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar.save(avatar_path)

                # Save the filename in the user model with forward slashes
                user.avatar = f'images/avatars/{filename}'

        # Commit changes to the database
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user', username=user.username))

    return render_template('profile.html', form=form, user=user)

@app.route('/courses', methods=['GET', 'POST'])
def get_courses():
    courses = db.session.scalars(sa.select(Course)).all()
    return render_template('courses_list.html', courses=courses)

@app.route('/courses/create', methods=['GET', 'POST'])
def create_course():
    form = CourseForm()
    
    form.course_prerequisites.choices = [(course.id, course.name) for course in Course.query.all()]

    if form.validate_on_submit():
        new_course = Course(
            type=form.type.data,
            name=form.name.data, 
            duration=form.duration.data
        )
        db.session.add(new_course)
        db.session.commit()

        for prerequisite_id in form.course_prerequisites.data:
            prerequisite = CoursePrerequisite(course_id=new_course.id, prerequisite_course_id=prerequisite_id)
            db.session.add(prerequisite)

        db.session.commit()
        flash('Course created successfully!', 'success')
        return redirect(url_for('get_courses'))

    return render_template('course_form.html', form=form)

@app.route("/courses/<int:course_id>", methods=["GET"])
def view_course(course_id):
    course = db.first_or_404(sa.select(Course).where(Course.id == course_id))
    groups = db.session.scalars(sa.select(Group).where(Group.course_group_id == course_id))
    return render_template('course_details.html', course=course, groups=groups)

@app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def edit_course(course_id):
    if not current_user.is_admin:
        return redirect(url_for('get_courses'))
    
    course = db.session.scalar(sa.select(Course).where(Course.id == course_id))
    form = CourseForm(obj=course)

    form.course_prerequisites.choices = [(course.id, course.name) for course in Course.query.all()]

    if form.validate_on_submit():
        course.type = form.type.data
        course.name = form.name.data
        course.duration = form.duration.data

        db.session.commit()

        for prerequisite in course.course_prerequisites:
            db.session.delete(prerequisite)

        for prerequisite_id in form.course_prerequisites.data:
            prerequisite = CoursePrerequisite(course_id=course.id, prerequisite_course_id=prerequisite_id)
            db.session.add(prerequisite)

        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('get_courses'))

    return render_template('course_form.html', form=form)

@app.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    if not current_user.is_admin:
        return redirect(url_for('get_courses'))
    
    course = db.first_or_404(sa.select(Course).where(Course.id == course_id))

    for prerequisite in course.course_prerequisites:
        db.session.delete(prerequisite)
    
    groups = db.session.scalars(sa.select(Group).where(Group.course_group_id == course_id)).all()
    for group in groups:
        for prerequisite in group.group_prerequisites:
            db.session.delete(prerequisite)
        db.session.delete(group)

    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    
    return redirect(url_for('get_courses'))

@app.route('/courses/<int:course_id>/groups', methods=['GET', 'POST'])
def get_groups(course_id):
    course = db.first_or_404(sa.select(Course).where(Course.id == course_id))
    groups = db.session.scalars(sa.select(Group).where(Group.course_group_id == course_id)).all()
    return render_template('groups_list.html', course=course, groups=groups)

@app.route('/courses/<int:course_id>/groups/create', methods=['GET', 'POST'])
@login_required
def create_group(course_id):
    if not current_user.is_admin:
        return redirect(url_for('get_groups', course_id=course_id))
    
    course = db.first_or_404(sa.select(Course).where(Course.id == course_id))
    form = GroupForm()
    
    # Populate the group_prerequisites field with existing groups
    form.group_prerequisites.choices = [(group.id, group.name) for group in Group.query.all()]

    if form.validate_on_submit():
        new_group = Group(
            name=form.name.data, 
            standard=form.standard.data,
            course_group=course
        )
        db.session.add(new_group)
        db.session.commit()

        # Add prerequisite groups
        for prerequisite_id in form.group_prerequisites.data:
            prerequisite = GroupPrerequisite(group_id=new_group.id, prerequisite_group_id=prerequisite_id)
            db.session.add(prerequisite)

        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('view_group', course_id=course_id, group_id=new_group.id))

    return render_template('group_form.html', form=form)

@app.route("/courses/<int:course_id>/groups/<int:group_id>", methods=["GET", "POST"])
@login_required
def view_group(course_id, group_id):
    group = db.first_or_404(sa.select(Group).where(Group.id==group_id, Group.course_group_id==course_id))
    subjects = db.session.scalars(sa.select(Subject).where(Subject.subject_group_id==group_id))
    
    form = SubjectForm()
    if not current_user.is_anonymous and current_user.is_admin:
        if form.validate_on_submit():
            new_subject = Subject(
                name = form.name.data,
                topics = form.topics.data,
                subject_group = group
            )
            db.session.add(new_subject)
            db.session.commit()
            return redirect(url_for("view_group", course_id=course_id, group_id=group_id))
    return render_template('group_details.html', form=form, group=group, subjects=subjects)

@app.route("/course/<int:course_id>/groups/<int:group_id>/edit", methods=["GET", "POST"])
@login_required
def edit_group(course_id, group_id):
    if not current_user.is_admin:
        return redirect(url_for('get_groups', course_id=course_id))
    
    group = db.first_or_404(sa.select(Group).where(Group.id == group_id, Group.course_group_id == course_id))
    form = GroupForm(obj=group)

    # Populate the group_prerequisites field with existing groups
    form.group_prerequisites.choices = [(group.id, group.name) for group in Group.query.all()]

    if form.validate_on_submit():
        group.name = form.name.data
        group.standard = form.standard.data

        db.session.commit()

        for prerequisite in group.group_prerequisites:
            db.session.delete(prerequisite)

        for prerequisite_id in form.group_prerequisites.data:
            prerequisite = GroupPrerequisite(group_id=group.id, prerequisite_group_id=prerequisite_id)
            db.session.add(prerequisite)

        db.session.commit()
        flash('Group updated successfully!', 'success')
        return redirect(url_for('get_groups', course_id=course_id))

    return render_template('group_form.html', form=form)

@app.route('/courses/<int:course_id>/groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(course_id, group_id):
    if not current_user.is_admin:
        return redirect(url_for('get_groups', course_id=course_id))
    
    group = db.first_or_404(sa.select(Group).where(Group.id == group_id, Group.course_group_id == course_id))
    for prerequisite in group.group_prerequisites:
        db.session.delete(prerequisite)

    db.session.delete(group)
    db.session.commit()
    flash('Group deleted successfully!', 'success')
    
    return redirect(url_for('get_groups'))

@app.route("/courses/<int:course_id>/groups/<int:group_id>/subjects/<subject_id>", methods=["POST"])
@login_required
def delete_subject(course_id, subject_id, group_id):
    if not current_user.is_anonymous and current_user.is_admin:
        subject = db.first_or_404(sa.select(Subject).where(Subject.id==subject_id, Subject.subject_group_id==group_id))

        db.session.delete(subject)
        db.session.commit()
        flash('Subjecty deleted successfully!', 'success')
    return redirect(url_for('view_group', course_id=course_id, group_id=group_id))