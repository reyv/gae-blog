import webapp2
import os
import jinja2
import models
import config
import util

from google.appengine.ext import db


class BaseRequestHandler(webapp2.RequestHandler):
    """Supplies a common template generation function.
    generate() augments the template variables."""

    def generate(self, template_name, template_values={}):
        values = {'blog_name': config.blog_name,
                    'twitter_url': config.twitter_url,
                    'google_plus_url': config.google_plus_url,
                    'linkedin_url': config.linkedin_url,
                    'tag_list': util.generate_tag_list(),
                    'archive_list': util.generate_archive_list()
                    }
        values.update(template_values)
        path = os.path.join(os.path.dirname(__file__), 'html/')
        jinja_environment = jinja2.Environment(
                                loader=jinja2.FileSystemLoader(path),
                                    autoescape=False)
        template = jinja_environment.get_template(template_name)
        self.response.out.write(template.render(values))

    def set_secure_cookie(self, name, value):
        hashed_user = util.make_secure_val(value)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/'
                                            % (name, hashed_user))

    def remove_secure_cookie(self, name):
        self.response.headers.add_header('Set-Cookie', '%s=; Path=/' % name)

    def check_secure_cookie(self):
        try:
            user_id_cookie_val = self.request.cookies.get('user_id')
            return util.check_secure_val(user_id_cookie_val)
        except AttributeError:
            return None


class NewPostHandler(BaseRequestHandler):
    """Generages and Handles New Blog Post Entires."""

    def get(self):
        if self.check_secure_cookie():
            self.generate('newpost.html', {
                            'user': 'admin'
                         })
        else:
            self.redirect('/blog/login')
            return

    def post(self):
        user = None
        subject = self.request.get('subject')
        content = self.request.get('content')
        content = content.replace('\n', '<br>')
        image_url = self.request.get('image_url')
        tag = self.request.get('tag')
        preview = self.request.POST.get('Preview', None)

        if subject and content and tag and image_url:
            if preview:
                preview = models.PostPreview(subject=subject,
                                                content=content,
                                                image_url=image_url,
                                                tag=tag,
                                                author=config.blog_author,
                                                key_name='preview')
                preview.put()
                self.redirect('/blog/newpost/preview')
                return
            else:
                blog_entry = models.BlogPost(subject=subject,
                                                content=content,
                                                image_url=image_url,
                                                tag=tag,
                                                author=config.blog_author)
                blog_entry.put()
                post_id = str(blog_entry.key().id())
                blog_entry.post_id = post_id
                blog_entry.put()

                #rerun query and update the cache.
                util.main_page_posts(True)
                util.tag_cache(tag, True)
                archive_year = blog_entry.created.strftime('%Y')
                util.archive_cache(archive_year, True)
                self.redirect('/blog/%s' % post_id)
                return
        else:
            self.generate('newpost.html', {
                            'newpost_error': 'All fields  are required!',
                            'subject': subject,
                            'content': content,
                            'image_url': image_url,
                            'tag': tag,
                            'user': user
                                })


class PreviewHandler(BaseRequestHandler):
    """Blog Post Preview Handler"""
    def get(self):
        user = None
        post_key = db.Key.from_path('PostPreview', 'preview')
        blog_post = models.PostPreview.get(post_key)

        if self.check_secure_cookie():
            user = 'admin'
        if not blog_post:
            self.generate('404.html', {})
        else:
            self.generate('preview.html', {
                                        'preview': blog_post,
                                        'user': user
                                         })


class BlogPostHandler(BaseRequestHandler):
    """Main Blog Page Handler"""
    def get(self):
        user = None
        blog_entries = util.main_page_posts()
        if self.check_secure_cookie():
            user = 'admin'
        self.generate('blog.html', {'blog_entries': blog_entries,
                        'user': user
                        })


class PermalinkHandler(BaseRequestHandler):
    def get(self, post_id):
        """Generator of permalink page for each blog entry"""
        user = None

        # postid variable gets passed in (i.e. /blog/(\d+))
        post_num = int(post_id)
        blog_post = models.BlogPost.get_by_id(post_num)

        if self.check_secure_cookie():
            user = 'admin'
        if not blog_post:
            self.generate('error.html', {})
        else:
            self.generate('blogpost.html', {
                            'blog_post': blog_post,
                            'post_id': post_id,
                            'user': user
                            })


class TagHandler(BaseRequestHandler):
    """Tag Page Handler"""
    def get(self, tag_name):
        tag_list = dict(util.generate_tag_list())
        user = None
        if self.check_secure_cookie():
            user = 'admin'
        if tag_name not in tag_list.keys():
            self.redirect('/blog')
            return
        else:
            blog_entries = util.tag_cache(tag_name)
            self.generate('blog.html', {
                            'blog_entries': blog_entries,
                            'user': user
                            })


class ArchiveHandler(BaseRequestHandler):
    """Archive Page Handler"""
    def get(self, archive_year):
        #previous_year = int(archive_year) + 1
        archive_list = dict(util.generate_archive_list())
        user = None
        if self.check_secure_cookie():
            user = 'admin'
        if archive_year not in archive_list.keys():
            self.redirect('/blog')
            return
        else:
            blog_entries = util.archive_cache(archive_year)
            self.generate('blog.html', {
                            'blog_entries': blog_entries,
                            'user': user
                            })


class LoginHandler(BaseRequestHandler):
    """Admin Login Page Handler"""
    def get(self):
        if self.check_secure_cookie():
            self.redirect('/blog')
            return
        else:
            self.generate('login.html', {})

    def post(self):
        username = str(self.request.get('username'))
        password = str(self.request.get('password'))

        user = models.Admin.login_validation(username)

        if user and util.valid_pw(username, password, user.admin_pw_hash):
            if util.valid_pw(username, password, user.admin_pw_hash):
                self.set_secure_cookie('user_id', str(user.key().id()))
                self.redirect('/blog/newpost')
                return
            else:
                self.generate('login.html', {
                                'username': username,
                                'error_login': 'Invalid rname and/or password'
                                 })
        else:
            self.generate('login.html', {
                            'error_login': 'User does not exist'
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
        user = None
        if self.check_secure_cookie():
            user = 'admin'
        self.generate('about.html', {
                        'user': user
                         })


class ContactHandler(BaseRequestHandler):
    """Contact Page Handler"""
    def get(self):
        user = None
        if self.check_secure_cookie():
            user = 'admin'
        self.generate('contact.html', {
                        'user': user
                        })

    def post(self):
        email_user = self.request.get('email_from')
        email_subject = self.request.get('email_subject')
        email_message = self.request.get('email_message')
        message = util.send_mail(email_user, email_subject, email_message)
        self.generate('contact.html', {
                                        'message': message,
                                        'user': 'admin'
                                    })


class AdminPrefHandler(BaseRequestHandler):
    """Admin Preferences Page Handler"""
    def get(self):
        user = None
        if not self.check_secure_cookie():
            self.redirect('/blog')
            return
        else:
            user = 'admin'
            self.generate('admin-pref.html', {'user': user})


class UsernameChangeHandler(BaseRequestHandler):
    """Change Username Page Handler"""
    def get(self):
        user = None
        if not self.check_secure_cookie():
            self.redirect('/blog')
            return
        else:
            user = 'admin'
        self.generate('username-change.html', {'user': user})

    def post(self):
        user = 'admin'
        new_username = str(self.request.get('new_username'))
        password = str(self.request.get('password'))

        user_id_cookie_val = self.request.cookies.get('user_id')
        u = models.Admin.get_user(user_id_cookie_val)

        if u and util.valid_pw(u.admin_username, password, u.admin_pw_hash):
            if util.valid_pw(u.admin_username, password, u.admin_pw_hash):
                u.admin_pw_hash = util.make_pw_hash(new_username, password)
                u.admin_username = new_username
                u.put()
                self.generate('username-change.html', {
                                'error_change_username': 'Change successful.',
                                'user': user
                                             })
            else:
                self.generate('username-change.html', {
                              'new_username': new_username,
                              'error_change_username': 'Invalid password',
                              'user': user
                              })
        else:
            self.generate('login.html', {'error_login': 'User does not exist'
                                        })


class PasswordChangeHandler(BaseRequestHandler):
    def get(self):
        user = None
        if not self.check_secure_cookie():
            self.redirect('/blog')
            return
        else:
            user = 'admin'
            self.generate('pw-change.html', {'user': user})

    def post(self):
        user = 'admin'
        password = str(self.request.get('password'))
        verify_password = str(self.request.get('verify_password'))

        if password != verify_password:
            self.generate('pw-change.html', {
                    'error_change_pw': 'Passwords do not match. Please retry.',
                    'user': user
                    })
        elif len(password) < 6:
            self.generate('pw-change.html', {
                    'error_change_pw': 'Password must be greater than 6 char.',
                    'user': user
                    })
        else:
            user_id_cookie_val = self.request.cookies.get('user_id')
            user = models.Admin.get_user(user_id_cookie_val)
            user.admin_pw_hash = util.make_pw_hash(
                                                user.admin_username, password)
            user.put()
            self.generate('pw-change.html', {
                                        'error_change_pw': 'Password changed.',
                                        'user': user
                                      })


class AdminHandler(BaseRequestHandler):
    #FOR TESTING PURPOSES ONLY
    def get(self):
        pw_hash = util.make_pw_hash(config.admin_username, config.admin_pw)
        admin = models.Admin(admin_username=config.admin_username,
                                admin_pw_hash=pw_hash)
        admin.put()
        self.redirect('/blog')
        return

app = webapp2.WSGIApplication([('/blog/?', BlogPostHandler),
                               ('/blog/newpost', NewPostHandler),
                               ('/blog/newpost/preview', PreviewHandler),
                               ('/blog/about', AboutHandler),
                               ('/blog/contact', ContactHandler),
                               ('/blog/login', LoginHandler),
                               ('/blog/logout', LogoutHandler),
                               ('/blog/admin', AdminHandler),
                               ('/blog/admin-pref', AdminPrefHandler),
                               ('/blog/pwchange', PasswordChangeHandler),
                               ('/blog/userchange', UsernameChangeHandler),
                               ('/blog/(\d+)', PermalinkHandler),
                               ('/blog/tags/(.*)', TagHandler),
                               ('/blog/archive/(\d{4})', ArchiveHandler)],
                                debug=True)

app.error_handlers[404] = util.handle_error
if not app.debug:
    app.error_handlers[500] = util.handle_error
