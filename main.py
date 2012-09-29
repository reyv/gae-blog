import webapp2, os, jinja2, models, urllib
from google.appengine.ext import db

class BaseRequestHandler(webapp2.RequestHandler):
  """Supplies a common template generation function.
     generate() augments the template variables."""

  def generate(self, template_name, template_values={}):
    values = {}
    values.update(template_values)  
    path = os.path.join(os.path.dirname(__file__),'html/')
    jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(path),autoescape=True)
    template = jinja_environment.get_template(template_name)
    self.response.out.write(template.render(template_values))

class NewPostHandler(BaseRequestHandler):
  """Generages and Handles New Blog Post Entires."""
  def get(self):
    self.generate('newpost.html',{})

  def post(self):
    subject = self.request.get('subject')
    content = self.request.get('content')
    content = content.replace('\n', '<br>')
    tag = self.request.get('tag')
    
    if subject and content and tag:
      blog_entry = models.BlogPost(subject=subject, content=content, tag=tag)
      blog_entry.put()
      post_id = str(blog_entry.key().id())
      blog_entry.post_id = post_id
      blog_entry.put()
      self.redirect('/blog/%s' %post_id)
    else:
      self.generate('newpost.html', {
		    'newpost_error':'Subject and content required.',
		    'subject':subject,
		    'content':content,
                    'tag':tag
                    })

class BlogPostHandler(BaseRequestHandler):
  """Main Blog Page Handler"""
  def get(self):
    blog_entries = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC LIMIT 10")

    tag_entries = db.GqlQuery("SELECT tag FROM BlogPost")
    tag_list = []
    for item in tag_entries:
      if item.tag not in tag_list:
        tag_list.append(item.tag)
    
    self.generate('blog.html',{'blog_entries':blog_entries,
                               'tag_list':tag_list})

class PermalinkHandler(BaseRequestHandler):
  def get(self, post_id):
    """Generator of permalink page for each blog entry"""
    post_num = int(post_id)           #postid variable gets passed in from the app variable (i.e. /blog/(\d+)) by placing () around desired url part
    blog_post = models.BlogPost.get_by_id(post_num)

    if not blog_post:
      self.generate('404.html',{})
    else:
      self.generate('blogpost.html',{
                    'blog_post':blog_post,
                    'post_id':post_id
                    })
      
class TagHandler(BaseRequestHandler):
  """Tag Page Handler"""
  def get(self, tag_name):
    blog_entries = db.GqlQuery("SELECT * FROM BlogPost WHERE tag='%s'" %unicode(tag_name))     
    self.generate('blog.html',{'blog_entries':blog_entries})

class AboutHandler(BaseRequestHandler):
  """About Page Handler"""
  def get(self):
    self.generate('about.html',{})

class ContactHandler(BaseRequestHandler):
  """Contact Page Handler"""
  def get(self):
    self.generate('contact.html',{})
    
    

app = webapp2.WSGIApplication([('/blog/?',BlogPostHandler),
                               ('/blog/newpost', NewPostHandler),
                               ('/blog/about', AboutHandler),
                               ('/blog/contact', ContactHandler),
                               ('/blog/(\d+)', PermalinkHandler),
                               ('/blog/tags/(\S+)', TagHandler)],
                                debug=True)

                              
#dev_appserver.py Dropbox/Programming/GAE/Udacity/Unit\ 2/HW1
