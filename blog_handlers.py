import webapp2
import blog_models
import blog_config
import blog_util
import logging

from google.appengine.ext import db


class BaseRequestHandler(webapp2.RequestHandler):
    """Supplies a common template generation function.
    generate() augments the template variables."""

    blog_values = {'blog_name': blog_config.blog_name,
                   'twitter_url': blog_config.twitter_url,
                   'google_plus_url': blog_config.google_plus_url,
                   'linkedin_url': blog_config.linkedin_url,
                   'tag_list': blog_util.generate_tag_list(),
                   'archive_list': blog_util.generate_archive_list()
                   }

    def generate(self, template_name, template_values={}):
        self.blog_values.update(template_values)
        self.response.out.write(blog_util.generate_template(template_name,
                                                            **self.blog_values)
                                                            )

    def set_secure_cookie(self, name, value):
        hashed_user = blog_util.make_secure_val(value)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/'
                                            % (name, hashed_user))

    def remove_secure_cookie(self, name):
        self.response.headers.add_header('Set-Cookie', '%s=; Path=/' % name)

    def check_secure_cookie(self):
        try:
            user_id_cookie_val = self.request.cookies.get('user_id')
            return blog_util.check_secure_val(user_id_cookie_val)
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
                preview = blog_models.PostPreview(subject=subject,
                                                content=content,
                                                image_url=image_url,
                                                tag=tag,
                                                author=blog_config.blog_author,
                                                key_name='preview')
                preview.put()
                self.redirect('/blog/newpost/preview')
                return
            else:
                blog_entry = blog_models.BlogPost(subject=subject,
                                                content=content,
                                                image_url=image_url,
                                                tag=tag,
                                                author=blog_config.blog_author)
                blog_entry.put()
                post_id = str(blog_entry.key().id())
                blog_entry.post_id = post_id
                blog_entry.put()

                #rerun query and update the cache.
                blog_util.main_page_posts(True)
                blog_util.tag_cache(tag, True)
                archive_year = blog_entry.created.strftime('%Y')
                blog_util.archive_cache(archive_year, True)
                blog_util.visits_cache(True)
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
        blog_post = blog_models.PostPreview.get(post_key)

        if self.check_secure_cookie():
            user = 'admin'
        if not blog_post:
            self.generate('error.html', {})
        else:
            self.generate('preview.html',
                         {'preview': blog_post,
                          'user': user})


class BlogPostHandler(BaseRequestHandler):
    """Main Blog Page Handler"""
    def get(self):
        user = None
        blog_entries = blog_util.main_page_posts()
        if self.check_secure_cookie():
            user = 'admin'
        self.generate('blog.html',
                     {'blog_entries': blog_entries,
                      'user': user})


class PermalinkHandler(BaseRequestHandler):
    def get(self, post_id):
        """Generator of permalink page for each blog entry"""
        user = None

        # postid variable gets passed in (i.e. /blog/(\d+))
        post_num = int(post_id)
        blog_post = blog_models.BlogPost.get_by_id(post_num)
        logging.error('DB write: Permalink Visit')
        blog_post.visits += 1
        blog_post.put()

        if self.check_secure_cookie():
            user = 'admin'
        if not blog_post:
            self.generate('error.html', {})
        else:
            self.generate('blogpost.html',
                          {'blog_post': blog_post,
                           'post_id': post_id,
                           'blog_author_link': blog_config.blog_author_link,
                           'user': user})


class TagHandler(BaseRequestHandler):
    """Tag Page Handler"""
    def get(self, tag_name):
        tag_list = dict(blog_util.generate_tag_list())
        user = None
        if self.check_secure_cookie():
            user = 'admin'
        if tag_name not in tag_list.keys():
            self.redirect('/blog')
            return
        else:
            blog_entries = blog_util.tag_cache(tag_name)
            self.generate('blog.html', {
                            'blog_entries': blog_entries,
                            'user': user
                            })


class ArchiveHandler(BaseRequestHandler):
    """Archive Page Handler"""
    def get(self, archive_year):
        archive_list = dict(blog_util.generate_archive_list())
        user = None
        if self.check_secure_cookie():
            user = 'admin'
        if archive_year not in archive_list.keys():
            self.redirect('/blog')
            return
        else:
            blog_entries = blog_util.archive_cache(archive_year)
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

        user = blog_models.Admin.login_validation(username)

        if user and blog_util.valid_pw(username, password, user.admin_pw_hash):
            if blog_util.valid_pw(username, password, user.admin_pw_hash):
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
        message = blog_util.send_mail(email_user, email_subject, email_message)
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
        u = blog_models.Admin.get_user(user_id_cookie_val)

        if u and blog_util.valid_pw(u.admin_username,
                                        password,
                                            u.admin_pw_hash):
            if blog_util.valid_pw(u.admin_username,
                                        password,
                                            u.admin_pw_hash):
                u.admin_pw_hash = blog_util.make_pw_hash(new_username,
                                                            password)
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
            user = blog_models.Admin.get_user(user_id_cookie_val)
            user.admin_pw_hash = blog_util.make_pw_hash(
                                                user.admin_username, password)
            user.put()
            self.generate('pw-change.html', {
                                'error_change_pw': 'Password changed.',
                                'user': user
                                })


class PostHistoryHandler(BaseRequestHandler):
    """Post History Handler"""
    def get(self):
        user = None
        blog_entries = blog_util.visits_cache()
        if self.check_secure_cookie():
            user = 'admin'
        self.generate('post-history.html', {'blog_entries': blog_entries,
                        'user': user
                        })


class AdminHandler(BaseRequestHandler):
    #FOR TESTING PURPOSES ONLY
    def get(self):
        pw_hash = blog_util.make_pw_hash(blog_config.admin_username,
                                            blog_config.admin_pw)
        admin = blog_models.Admin(admin_username=blog_config.admin_username,
                                admin_pw_hash=pw_hash)
        admin.put()
        self.redirect('/blog')
        return
