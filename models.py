import config
from google.appengine.ext import db

class BlogPost(db.Model):
  """Model class for blog posts"""
  subject = db.StringProperty(required=True)
  content = db.TextProperty(required=True)
  created = db.DateTimeProperty(auto_now_add = True)
  last_modified = db.DateTimeProperty(auto_now = True)
  post_id = db.StringProperty()
  tag = db.StringProperty(required=True)
  author = db.StringProperty()


class Admin(db.Model):
  """Model class for Admin login"""
  admin_username = db.StringProperty(required=True, default=config.admin_username)
  admin_pw_hash = db.StringProperty(required=True, default=config.admin_pw)
  
  @classmethod
  def login_validation(cls, username):
    try:
      q = db.GqlQuery("SELECT * from Admin WHERE admin_username='%s'" %username)
      return q[0]
    except IndexError:
      return None
