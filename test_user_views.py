"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

# Missing tests: login w/ wrong pw, login w/ wrong username, edit profile w/
#   wrong pw, search for user with search term, homepage display when logged
#   in with following/followers

import os
from unittest import TestCase
from flask import session

from models import db, Message, User

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


class UserViewTestCase(TestCase):
    """Test views for Users."""

    def setUp(self):
        """Create test client, add sample data."""

        Message.query.delete()
        User.query.delete()

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

        self.testuser2 = User.query.filter_by(username="testuser2").first()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

########################################### LOGIN/LOGOUT TESTS ####################################################
    
    def test_login(self):
        """Can user log in with valid credentials?"""

        with self.client as c: 
            response = c.post(
                            "/login",
                            data={"username": "testuser", "password": "password"},
                            follow_redirects=True
                            )

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("User Logged In", html)
            self.assertEqual(session[CURR_USER_KEY], self.testuser.id)



    def test_logout(self):
        """Can user logout successfully?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.post("/logout", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Successfully logged out", html)

            with self.assertRaises(KeyError): 
                session[CURR_USER_KEY]

########################################### VIEW FOLLOWING/FOLLOWER TESTS ####################################################
    
    def test_logged_in_user_view_others_followers(self):
        """Can a logged in user view others' followers page"""

        with self.client as c:  
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.get(f"/users/{self.testuser2.id}/followers")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(f"@{self.testuser2.username}", html)


    def test_logged_in_user_view_others_following(self):
        """Can a logged in user view others' following page"""

        with self.client as c:  
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.get(f"/users/{self.testuser2.id}/following")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(f"@{self.testuser2.username}", html)  


    def test_logged_out_view_others_followers(self):
        """Can not access others' followers page when logged out"""   

        with self.client as c:
            response = c.get(f"/users/{self.testuser2.id}/followers",
                            follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)

    
    def test_logged_out_view_others_following(self):
        """Can not access others' following page when logged out"""   

        with self.client as c:
            response = c.get(f"/users/{self.testuser2.id}/following",
                            follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)

########################################### USER TESTS ####################################################

    def test_get_invalid_user(self):
        """Can get details of invalid user?"""

        with self.client as c:
            response = c.get("/users/0")

            self.assertEqual(response.status_code, 404)


    def test_get_existing_user(self):
        """Can get details of existing user?"""

        with self.client as c:
            response = c.get(f"/users/{self.testuser.id}")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(f"@{self.testuser.username}", html)
    
########################################### EDIT PROFILE TESTS ####################################################

    def test_show_edit_own_profile(self):
        """Can display edit profile page when logged in?"""

        with self.client as c: 
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get("/users/profile")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Test Edit User Profile", html)

    
    def test_post_edit_own_profile(self): 
        """Can post to edit profile page when logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post("/users/profile",
                              data={
                                'bio': 'updated bio',
                                'password': 'password'
                                },
                              follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("updated bio", html)

    def test_show_edit_profile_not_logged_in(self):
        """Can not see edit profile page when not logged in"""

        with self.client as c:
            response = c.get("/users/profile", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)

########################################### FOLLOW/UNFOLLOW TESTS ####################################################

    def test_follow_user(self):
        """Can user follow another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post(f"/users/follow/{self.testuser2.id}", follow_redirects=True)
            html = response.get_data(as_text=True)

            user = User.query.get(sess[CURR_USER_KEY])

            self.assertEqual(response.status_code, 200)
            self.assertIn(f"@{self.testuser2.username}", html)
            self.assertEqual(len(user.following), 1)
    
    def test_unfollow_user(self):
        """Can user unfollow another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # user is following user2
            c.post(f"/users/follow/{self.testuser2.id}", follow_redirects=True)

            # user is unfollowing user2
            unfollow_response = c.post(f"/users/stop-following/{self.testuser2.id}", follow_redirects=True)
            html = unfollow_response.get_data(as_text=True)

            user = User.query.get(sess[CURR_USER_KEY])

            self.assertEqual(unfollow_response.status_code, 200)
            self.assertNotIn(f"@{self.testuser2.username}", html)
            self.assertEqual(len(user.following), 0)

    def test_follow_user_not_logged_in_fail(self):
        """Can not user follow another user when not logged in"""

        with self.client as c:
            response = c.post(f"/users/follow/{self.testuser2.id}", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)
            
    def test_unfollow_user_not_logged_in_fail(self):
        """Can not user unfollow another user when not logged in"""

        with self.client as c:
            response = c.post(f"/users/stop-following/{self.testuser2.id}", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)

########################################### SEARCH TESTS ####################################################

    def test_search_user(self):
        """Can search for another user with search?"""

        with self.client as c:
            response = c.get("/users")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(f"@{self.testuser.username}", html)

    #test search for specific user

########################################### DELETE TESTS ####################################################
        
    def test_delete_user(self):
        """Can delete user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post("/users/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("User successfully deleted", html)

            # checks user successfully deleted
            self.assertEqual(User.query.count(), 1)

    def test_delete_user_not_logged_in(self):
        """Can not delete user when not logged in"""

        with self.client as c:
            response = c.post("/users/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)

            # checks user was not deleted
            self.assertEqual(User.query.count(), 2)