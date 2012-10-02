import webapp2, os, jinja2, models, urllib
from collections import Counter
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

  def generate_tag_list(self):
    tag_entries = db.GqlQuery("SELECT tag FROM BlogPost")
    tags_all = [str(item.tag) for item in tag_entries]    #excecute query
    c = Counter(tags_all)                                 #provides dict with count of each tag
    return sorted(c.iteritems())                          #returns list w/ tuples in alphabetic order

class NewPostHandler(BaseRequestHandler):
  """Generages and Handles New Blog Post Entires."""
  def get(self):
    self.generate('newpost.html',{
                  'tag_list':self.generate_tag_list()
                  })

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
                    'tag':tag,
                    'tag_list':self.generate_tag_list()
                    })

class BlogPostHandler(BaseRequestHandler):
  """Main Blog Page Handler"""
  def get(self):
    blog_entries = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC LIMIT 10")  
    self.generate('blog.html',{'blog_entries':blog_entries,
                               'tag_list':self.generate_tag_list()
                  })

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
                    'post_id':post_id,
                    'tag_list':self.generate_tag_list()
                    })
   
class TagHandler(BaseRequestHandler):
  """Tag Page Handler"""
  def get(self, tag_name):
    tag_list = dict(self.generate_tag_list())
    if tag_name not in tag_list.keys():
      self.generate('blog.html', {
                    'error_message':'Sorry, that tag has not been found!'
                    })
    else:
      blog_entries = db.GqlQuery("SELECT * FROM BlogPost WHERE tag='%s'" %tag_name) 
      self.generate('blog.html',{
                    'blog_entries':blog_entries,
                    'tag_list':self.generate_tag_list()
                    })

class AboutHandler(BaseRequestHandler):
  """About Page Handler"""
  def get(self):
    self.generate('about.html',{
                  'tag_list':self.generate_tag_list()
                  })

class ContactHandler(BaseRequestHandler):
  """Contact Page Handler"""
  def get(self):
    self.generate('contact.html',{
                  'tag_list':self.generate_tag_list()
                  })
    
app = webapp2.WSGIApplication([('/blog/?',BlogPostHandler),
                               ('/blog/newpost', NewPostHandler),
                               ('/blog/about', AboutHandler),
                               ('/blog/contact', ContactHandler),
                               ('/blog/(\d+)', PermalinkHandler),
                               ('/blog/tags/(.*)', TagHandler)],
                                debug=True)
