"""Like View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_like_views.py


import os
from unittest import TestCase
from flask import session

from models import db, Message, User, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class LikeViewTestCase(TestCase):
    """Test views for Like."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                            email="test2@test.com",
                            password="password",
                            image_url=None)
        db.session.commit()


        self.message = Message(text="test message", user_id=self.testuser.id)
        db.session.add(self.message)
        db.session.commit()

        self.testuser2 = User.query.filter_by(username="testuser2").first()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_logged_in_user_view_others_likes(self):
        """Can a logged in user view others' liked messages page"""

        with self.client as c:  
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.get(f"/users/{self.testuser2.id}/likes")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(f"@{self.testuser2.username}", html)


    def test_logged_out_view_others_likes(self):
        """Can access others' liked messages page when logged out?"""   

        with self.client as c:
            response = c.get(f"/users/{self.testuser2.id}/likes",
                            follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)