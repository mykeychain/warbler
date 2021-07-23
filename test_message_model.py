"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from sqlalchemy.exc import IntegrityError

from models import db, User, Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        Message.query.delete()
        User.query.delete()

        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url=""
        )

        db.session.add(user)
        db.session.commit()
        self.user = user

        message = Message(
            text="test message text",
            user_id=user.id
        )

        db.session.add(message)
        db.session.commit()
        self.message = message

        self.client = app.test_client()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="text",
            user_id=self.user.id
        )

        db.session.add(m)
        db.session.commit()

        #query for Message and test 

        self.assertIsInstance(m, Message)
        self.assertEqual(len(m.text), 4)
        self.assertEqual(len(m.liked_users), 0)


    def test_message_no_text(self):
        """Does Message fail to create message when no text given?"""

        m = Message(
            user_id=self.user.id
        )
        db.session.add(m)
        with self.assertRaises(IntegrityError):
            db.session.commit()


    def test_repr_method(self):
        """Does repr method work?"""

        self.assertEqual(f'<Message #{self.message.id}: {self.message.text} by {self.message.user_id}>', self.message.__repr__())

    
        