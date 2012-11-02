import blog_config
from google.appengine.ext import db


class BlogPost(db.Model):
    """Model class for blog posts"""
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    post_id = db.StringProperty()
    image_url = db.StringProperty(required=True)
    tag = db.StringProperty(required=True)
    author = db.StringProperty()
    visits = db.IntegerProperty(default=0)


class PostPreview(BlogPost):
    """Model class for blog post previews"""
    pass


class Admin(db.Model):
    """Model class for Admin login"""
    admin_username = db.StringProperty(required=True,
                                       default=blog_config.admin_username
                                       )
    admin_pw_hash = db.StringProperty(required=True,
                                      default=blog_config.admin_pw
                                      )

    @classmethod
    def login_validation(cls, username):
        try:
            q = db.GqlQuery("SELECT * from Admin WHERE admin_username= :1",
                            username
                            )
            return q[0]
        except IndexError:
            return None

    @classmethod
    def get_user(cls, user_id_cookie_val):
        user_id = user_id_cookie_val.split('|')[0]
        user_key = db.Key.from_path('Admin', int(user_id))
        return db.get(user_key)


class SubscribeEmail(db.Model):
    """Model class for Receiving Subscribe Emails"""
    email = db.EmailProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
