"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

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

        Follows.query.delete()
        Message.query.delete()
        User.query.delete()

        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url=""
        )

        user2 = User.signup(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD",
            image_url=""
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


    def test_repr_method(self):
        """Does repr method work?"""

        self.assertEqual(f'<User #{self.user.id}: {self.user.username}, {self.user.email}>', self.user.__repr__())

########################################### FOLLOWING/FOLLOWER TESTS ####################################################

    def test_is_following(self):
        """Does is_following detect user1 is following user2?"""
        
        self.user.following.append(self.user2)
        db.session.commit()
        self.assertEqual(self.user2.followers[0].id, self.user.id)
        self.assertEqual(self.user.following[0].id, self.user2.id)
        self.assertTrue(self.user.is_following(self.user2))


    def test_is_not_following(self):
        """Does is_following detect user1 is not following user2?"""
        
        self.assertFalse(self.user.is_following(self.user2))


    def test_is_followed_by(self):
        """Does is_followed_by detect user1 is followed by user12"""
        
        self.user2.following.append(self.user)
        db.session.commit()
        self.assertEqual(self.user.followers[0].id, self.user2.id)
        self.assertEqual(self.user2.following[0].id, self.user.id)
        self.assertTrue(self.user.is_followed_by(self.user2))


    def test_is_not_followed_by(self):
        """Does is_followed_by detect user1 is not followed by user12"""
        
        self.assertFalse(self.user.is_followed_by(self.user2))

########################################### SIGNUP TESTS ####################################################

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

        # user = User.query.filter()
        # self.assertTrue( user.password.startsWith('$2b$'))
        #query for the user

        self.assertIsInstance(u, User)
        self.assertNotEqual("HASHED_PASSWORD", u.password)
        self.assertEqual('tester', u.username)


    def test_user_signup_fail(self):
        """Does User.signup fail to create a new user if any of the validations
           (e.g. uniqueness, non-nullable fields) fail?"""

        u = User.signup(
            username="testuser", #this is a duplicate username
            password="HASHED_PASSWORD",
            email="test@email.com",
            image_url=""
        )

        db.session.add(u)

        with self.assertRaises(IntegrityError):
            db.session.commit()

########################################### AUTHENTICATE TESTS ####################################################

    def test_user_authenticate_success(self):
        """Does User.authenticate return user when given valid username and password?"""

        existing_user = User.signup(
            username="tester",
            password="HASHED_PASSWORD",
            email="tester@test.com",
            image_url=""
        )

        db.session.add(existing_user)
        db.session.commit()

        user = User.authenticate("tester", "HASHED_PASSWORD")

        self.assertIsInstance(user, User)


    def test_user_authenticate_username_fail(self):
        """Does User.authenticate fail to return user when given invalid username?"""

        user = User.authenticate("invalid_username", "HASHED_PASSWORD")
        
        self.assertFalse(user)

    
    def test_user_authenticate_password_fail(self):
        """Does User.authenticate fail to return user when given invalid password?"""

        user = User.authenticate("testuser", "Wrong_Password")

        self.assertFalse(user)
        
        

