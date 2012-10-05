import webapp2, os, jinja2, models, urllib, config, secure
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

  def set_secure_cookie(self, name, value):
    hashed_user = secure.make_secure_val(value)
    self.response.headers.add_header('Set-Cookie','%s=%s; Path=/' %(name, hashed_user))

  def remove_secure_cookie(self, name):
    self.response.headers.add_header('Set-Cookie','%s=; Path=/' %name)

  def check_secure_cookie(self):
    user_id_cookie_val = self.request.cookies.get('user_id')
    user_id = user_id_cookie_val.split('|')[0]
    return secure.check_secure_val(user_id_cookie_val)
   
class NewPostHandler(BaseRequestHandler):
  """Generages and Handles New Blog Post Entires."""

  def get(self):
    if self.check_secure_cookie():
      self.generate('newpost.html',{
                    'tag_list':self.generate_tag_list(),
                    'user':'admin'
                    })
    else:
      self.redirect('/blog/login')
      return
   
  def post(self):
    subject = self.request.get('subject')
    content = self.request.get('content')
    content = content.replace('\n', '<br>')
    tag = self.request.get('tag')
    
    if subject and content and tag:
      blog_entry = models.BlogPost(subject=subject, content=content, tag=tag, author=config.blog_author)
      blog_entry.put()
      post_id = str(blog_entry.key().id())
      blog_entry.post_id = post_id
      blog_entry.put()
      self.redirect('/blog/%s' %post_id)
      return
    else:
      self.generate('newpost.html', {
		    'newpost_error':'Subject and content required.',
		    'subject':subject,
		    'content':content,
                    'tag':tag,
                    'tag_list':self.generate_tag_list(),
                    'user':'admin'
                    })

class BlogPostHandler(BaseRequestHandler):
  """Main Blog Page Handler"""
  def get(self):
    user = None
    blog_entries = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC LIMIT 10")  
    if self.check_secure_cookie():
      user = 'admin'
    self.generate('blog.html',{'blog_entries':blog_entries,
                               'tag_list':self.generate_tag_list(),
                               'user':user
                  })

class PermalinkHandler(BaseRequestHandler):
  def get(self, post_id):
    """Generator of permalink page for each blog entry"""
    user=None
    post_num = int(post_id)           #postid variable gets passed in from the app variable (i.e. /blog/(\d+)) by placing () around desired url part
    blog_post = models.BlogPost.get_by_id(post_num)
    
    if self.check_secure_cookie():
      user = 'admin'
    if not blog_post:
      self.generate('404.html',{})
    else:
      self.generate('blogpost.html',{
                    'blog_post':blog_post,
                    'post_id':post_id,
                    'tag_list':self.generate_tag_list(),
                    'user':user
                    })
   
class TagHandler(BaseRequestHandler):
  """Tag Page Handler"""
  def get(self, tag_name):
    tag_list = dict(self.generate_tag_list())
    user=None
    if self.check_secure_cookie():
      user='admin'
    if tag_name not in tag_list.keys():
      self.redirect('/blog')
      return
    else:
      blog_entries = db.GqlQuery("SELECT * FROM BlogPost WHERE tag='%s'" %tag_name) 
      self.generate('blog.html',{
                    'blog_entries':blog_entries,
                    'tag_list':self.generate_tag_list(),
                    'user':user
                    })

class LoginHandler(BaseRequestHandler):
  """Admin Login Page Handler"""
  def get(self):
    if self.check_secure_cookie():
      self.redirect('/blog')
    else:
      self.generate('login.html',{})
    
  def post(self):
    username = str(self.request.get('username'))
    password = str(self.request.get('password'))

    user = models.Admin.login_validation(username)

    if user and secure.valid_pw(username, password, user.admin_pw_hash):
      if secure.valid_pw(username, password, user.admin_pw_hash):
        self.set_secure_cookie('user_id',str(user.key().id()))
        self.redirect('/blog/newpost')
        return
      else:
        self.generate('login.html', {
                      'username':username,
                      'error_login':'Invalid username and/or password'
                      })
    else:
      self.generate('login.html', {
                    'error_login':'User does not exist'
                    })

class LogoutHandler(BaseRequestHandler):
  """Logout Handler"""
  def get(self):
    self.remove_secure_cookie('user_id')
    self.redirect('/blog')
    return
  
class AboutHandler(BaseRequestHandler):
  """About Page Handler"""
  def get(self):
    user=None
    if self.check_secure_cookie():
      user = 'admin'
    self.generate('about.html',{
                  'tag_list':self.generate_tag_list(),
                  'user':user
                  })

class ContactHandler(BaseRequestHandler):
  """Contact Page Handler"""
  def get(self):
    user=None
    if self.check_secure_cookie():
      user = 'admin'
    self.generate('contact.html',{
                  'tag_list':self.generate_tag_list(),
                  'user':user
                  })
    
class PasswordChangeHandler(BaseRequestHandler):
  """Change Password Page Handler"""
  def get(self):
    user = None
    if not self.check_secure_cookie():
      self.redirect('/blog')
      return
    else:
      user='admin'
      self.generate('pw-change.html',{'user':user})
    
  def post(self):
    user = 'admin'
    password = str(self.request.get('password'))
    verify_password = str(self.request.get('verify_password'))

    if password != verify_password:
      self.generate('pw-change.html', {
                    'error_change_pw':'Passwords do not match. Please retry.',
                    'user':user
                    })
    elif len(password) < 6:
      self.generate('pw-change.html', {
                    'error_change_pw':'Password must be greater than 6 characters.',
                    'user':user
                    })
    else:
      self.remove_secure_cookie('user-id')
      user_id_cookie_val = self.request.cookies.get('user_id')
      user_id = user_id_cookie_val.split('|')[0]
      user_key = db.Key.from_path('Admin', int(user_id))
      user = db.get(user_key)
      user.admin_pw_hash = secure.make_pw_hash(user.admin_username, password)
      user.put()
      self.set_secure_cookie('user-id', str(user_id))
      self.generate('pw-change.html',{'error_change_pw': 'Password change successful.',
                                      'user':user
                                      })


class AdminHandler(BaseRequestHandler):
  #FOR TESTING PURPOSES ONLY
  def get(self):
    pw_hash = secure.make_pw_hash(config.admin_username, config.admin_pw)
    admin = models.Admin(admin_username = config.admin_username, admin_pw_hash = pw_hash)
    admin.put()
    self.redirect('/blog')
    return
 
app = webapp2.WSGIApplication([('/blog/?',BlogPostHandler),
                               ('/blog/newpost', NewPostHandler),
                               ('/blog/about', AboutHandler),
                               ('/blog/contact', ContactHandler),
                               ('/blog/login', LoginHandler),
                               ('/blog/logout', LogoutHandler),
                               ('/blog/admin',AdminHandler),
                               ('/blog/pwchange',PasswordChangeHandler),
                               ('/blog/(\d+)', PermalinkHandler),
                               ('/blog/tags/(.*)', TagHandler)],
                                debug=True)
