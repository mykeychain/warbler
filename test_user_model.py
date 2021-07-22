"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Like

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Like.query.delete()

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(user)
        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )
        db.session.add_all([user, user2])
        db.session.commit()
        self.user = user
        self.user2 = user2


        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test3@test.com",
            username="testuser3",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    # def test_repr_method(self):
    #     """Does repr method work?"""

    #     self.assertEqual(f'<User #{self.user.id}: {self.user.username}, {self.user.email}>', self.user)

    def test_is_following(self):
        """Does is_following detect user1 is following user2?"""
        
        self.user.following.append(self.user2)
        self.assertTrue(self.user.is_following(self.user2))

    def test_is_not_following(self):
        """Does is_following detect user1 is not following user2?"""
        
        self.assertFalse(self.user.is_following(self.user2))

    def test_is_followed_by(self):
        """Does is_followed_by detect user1 is followed by user12"""
        
        self.user2.following.append(self.user)
        self.assertTrue(self.user.is_followed_by(self.user2))

    def test_is_not_followed_by(self):
        """Does is_followed_by detect user1 is not followed by user12"""
        
        self.assertFalse(self.user.is_followed_by(self.user2))

    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        u = User.signup(
            username="tester",
            password="HASHED_PASSWORD",
            email="tester@test.com",
            image_url=""
        )

        db.session.add(u)
        db.session.commit()

        self.assertIsInstance(u, User)
        self.assertNotEqual("HASHED_PASSWORD", u.password)
        self.assertEqual('tester', u.username)

    def test_user_signup_fail(self):
        """Does User.signup fail to create a new user if any of the validations
           (e.g. uniqueness, non-nullable fields) fail?"""

        u = User.signup(
            username="test",
            password="HASHED_PASSWORD",
            email="",
            image_url=""
        )

        db.session.add(u)
        db.session.commit()

        # self.assertRaises()
        # self.assertEqual('tester', self.username)


