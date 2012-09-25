import webapp2, os, jinja2, re
from google.appengine.ext import db

class BaseRequestHandler(webapp2.RequestHandler):
  """Supplies a common template generation function.
     generate() augments the template variables."""

  def generate(self, template_name, template_values={}):
    values = {}
    values.update(template_values)  
    path = os.path.join(os.path.dirname(__file__),'static/html/')
    jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(path),autoescape=True)
    template = jinja_environment.get_template(template_name)
    self.response.out.write(template.render(template_values))

class NewPostHandler(BaseRequestHandler):
  
  def get(self):
    self.generate('newpost.html',{})

  def post(self):
    subject = self.request.get('subject')
    content = self.request.get('content')
    content = content.replace('\n', '<br>')
    
    if valid_string(subject) and valid_string(content):
      blog_entry = BlogPost(subject=subject, content=content)
      blog_entry.put()
      post_id = str(blog_entry.key().id())
      self.redirect('/blog/%s' %post_id)
    else:
      self.generate('newpost.html', {
		    'newpost_error':'Subject and content required.',
		    'subject':subject,
		    'content':content  
      })

class BlogPostHandler(BaseRequestHandler):
  def get(self):
    blog_entries = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC LIMIT 10")     
    self.generate('blog.html',{'blog_entries':blog_entries})

class PermalinkHandler(BaseRequestHandler):
  def get(self, postid):
    post_num = int(postid)           #postid variable gets passed in from the app variable (i.e. /blog/(\d+)) by placing () around desired url part
    blog_post = BlogPost.get_by_id(post_num)

    if not blog_post:
      self.error(404)
    else:
      self.generate('blogpost.html',{'blog_post':blog_post})
    
class BlogPost(db.Model):
  subject = db.TextProperty(required=True)
  content = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add = True)
  last_modified = db.DateTimeProperty(auto_now = True)
       
def valid_string(item):
    if item:
      return True

app = webapp2.WSGIApplication([('/blog/?',BlogPostHandler),
                               ('/blog/newpost', NewPostHandler),
                               ('/blog/(\d+)', PermalinkHandler)],
                                debug=True)

                              
#dev_appserver.py Dropbox/Programming/GAE/Udacity/Unit\ 2/HW1
