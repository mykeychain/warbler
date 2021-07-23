import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm, CsrfOnlyForm
from models import db, connect_db, User, Message
import pdb
from functools import wraps

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout

def login_required(func):
    """Checks if user is logged in, if not then redirect to login page."""

    @wraps(func)
    def check_logged_in(*args, **kwargs): 
        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/") 
        else: 
            return func(*args, **kwargs)
    
    return check_logged_in


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


@app.before_request
def add_csrf_only_form():
    """Add a CSRF-only form so that every route can use it."""
    g.csrf_form = CsrfOnlyForm()



def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]



@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout', methods=["POST"])
def logout():
    """Handle logout of user."""

    if g.csrf_form.validate_on_submit():
        do_logout()
    
        flash('Successfully logged out')

    return redirect(url_for('login'))


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user)


@app.route('/users/<int:user_id>/following')
@login_required
def show_following(user_id):
    """Show list of people this user is following."""

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
@login_required
def users_followers(user_id):
    """Show list of followers of this user."""

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
@login_required
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if g.csrf_form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()

    return redirect(url_for('show_following', user_id=g.user.id))


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
@login_required
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if g.csrf_form.validate_on_submit():
        followed_user = User.query.get(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()

    return redirect(url_for('show_following', user_id=g.user.id))



@app.route('/users/profile', methods=["GET", "POST"])
@login_required
def profile():
    """Update profile for current user."""
    
    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        user = User.authenticate(g.user.username,
                                 form.password.data)
        if user:
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            user.header_image_url = form.header_image_url.data
            user.bio = form.bio.data or None
            user.location = form.location.data or None

            db.session.commit()
            return redirect(url_for('users_show', user_id=g.user.id))
        else:
            flash("Incorrect password")
            return redirect(url_for("profile"))

    return render_template("users/edit.html", form=form)



@app.route('/users/delete', methods=["POST"])
@login_required
def delete_user():
    """Delete user."""

    if g.csrf_form.validate_on_submit():
        do_logout()

        Message.query.filter(Message.user_id == g.user.id).delete()
        db.session.delete(g.user)
        db.session.commit()

        flash("User successfully deleted")
    return redirect(url_for("signup"))



##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
@login_required
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(url_for("users_show", user_id=g.user.id))

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
@login_required
def messages_destroy(message_id):
    """Delete a message."""

    if g.csrf_form.validate_on_submit():
        msg = Message.query.get_or_404(message_id)
        db.session.delete(msg)
        db.session.commit()

    return redirect(url_for("users_show", user_id=g.user.id))


##############################################################################
# Likes

@app.route('/users/like/<int:message_id>', methods=['POST'])
@login_required
def like_message(message_id):
    """Like a message for current user."""

    if g.csrf_form.validate_on_submit():
        liked_message = Message.query.get_or_404(message_id)
        g.user.liked_messages.append(liked_message)
        db.session.commit()

    return redirect("/")


@app.route('/users/unlike/<int:message_id>', methods=['POST'])
@login_required
def unlike_message(message_id):
    """Unlike a message for current user."""

    if g.csrf_form.validate_on_submit():
        liked_message = Message.query.get_or_404(message_id)
        g.user.liked_messages.remove(liked_message)
        db.session.commit()

    return redirect("/")

@app.route('/users/<int:user_id>/likes')
@login_required
def users_likes(user_id):
    """Show list of likes of this user."""

    user = User.query.get_or_404(user_id)
    return render_template('users/likes.html', user=user)



##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        following_ids = [user.id for user in g.user.following]
        following_ids.append(g.user.id)
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
                    
        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


@app.errorhandler(404)
def show_404(e): 
    """Show 'page-not-found' when 404 error."""

    return render_template('404.html'), 404




##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
