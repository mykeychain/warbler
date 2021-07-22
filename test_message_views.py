"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from sqlalchemy.exc import NoResultFound

from models import db, connect_db, Message, User

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_delete_message(self):
        """Can user delete their own message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # adds message
            c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.one()

            # deletes message
            delete_resp = c.post(f"/messages/{msg.id}/delete")

            self.assertEqual(delete_resp.status_code, 302)
            self.assertEqual(Message.query.count(), 0)


    def test_find_invalid_message(self):
        """Can get a message with message id that does not exist?"""

        with self.client as c:
        
            resp = c.get("/messages/0")

            self.assertEqual(resp.status_code, 404)
    

    def test_show_message(self):
        """Can see message details?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # adds message
            c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.one()

            # gets message
            resp = c.get(f"/messages/{msg.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test Message - For Testing", html)


    def test_add_message_not_logged_in(self):
        """Can add a message when not logged in?"""

        with self.client as c:
            # we do not set the session so we are not "logged in"
            # we should be redirected to root
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)
    

    def test_delete_message_not_logged_in(self):
        """Can delete a message when not logged in?"""

        with self.client as c:
            # we do not set the session so we are not "logged in"
            # we should be redirected to root
            resp = c.post("/messages/1/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    
