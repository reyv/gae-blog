from google.appengine.ext import db

class BlogPost(db.Model):
  """Model class for blog posts"""
  subject = db.StringProperty(required=True)
  content = db.TextProperty(required=True)
  created = db.DateTimeProperty(auto_now_add = True)
  last_modified = db.DateTimeProperty(auto_now = True)
  post_id = db.StringProperty()
  tag = db.StringProperty(required=True)
