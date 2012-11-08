from google.appengine.ext import db

import config
import util


class BlogPost(db.Model):
    """Model class for blog posts"""
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    post_id = db.StringProperty()
    image_url = db.StringProperty(required=True)
    tag = db.StringProperty(required=True)
    author = db.StringProperty(default=config.blog_author)
    visits = db.IntegerProperty(default=0)


class PostPreview(BlogPost):
    """Model class for blog post previews"""
    pass


class Admin(db.Model):
    """Model class for Admin login"""
    admin_username = db.StringProperty(default=config.admin_username)
    admin_pw_hash = db.StringProperty(default=config.admin_pw)

    @classmethod
    def login_validation(cls, username):
        """Provides login validation for login"""
        try:
            q = db.GqlQuery("SELECT * from Admin WHERE admin_username= :1",
                            username)
            return q[0]
        except IndexError:
            return None

    @classmethod
    def change_username(cls, new_username, pw):
        """Function to change Admin username in preferences page.
           Password re-hashing is required since the stored password
           hashes are a function of the username.
        """
        if not new_username or not pw:
            return 'A new username and or password is required. Retry.'
        elif len(new_username) < 6:
            return 'Username must be greater than 6 characters'
        else:
            admin_key = db.Key.from_path('Admin', 'admin_key_name')
            admin = Admin.get(admin_key)
            if not util.valid_pw(admin.admin_username, pw,
                                      admin.admin_pw_hash):
                return 'Invalid Password. Please Retry.'
            else:
                admin.admin_username = new_username
                pw_hash = util.make_pw_hash(new_username, pw)
                admin.admin_pw_hash = pw_hash
                admin.put()
                return 'Username change was successful!'

    @classmethod
    def change_password(cls, password, verify_password):
        """Function to change Admin password in preferences page"""
        if password != verify_password:
            return 'Passwords do not match. Please retry.'
        elif len(password) < 6:
            return 'Password must be greater than 6 characters.'
        else:
            admin_key = db.Key.from_path('Admin', 'admin_key_name')
            admin = Admin.get(admin_key)
            pw_hash = util.make_pw_hash(admin.admin_username, password)
            admin.admin_pw_hash = pw_hash
            admin.put()
            return 'Password changed.'


class SubscribeEmail(db.Model):
    """Model class for Receiving Subscribe Emails"""
    email = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
