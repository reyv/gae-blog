import cgi
import logging

import webapp2
from google.appengine.ext import db

import blog_models
import blog_config
import blog_util


class BaseRequestHandler(webapp2.RequestHandler):
    """Base Handler for all Requests"""
    blog_values = {'blog_name': blog_config.blog_name,
                   'blog_desc': blog_config.blog_desc,
                   'twitter_url': blog_config.twitter_url,
                   'google_plus_url': blog_config.google_plus_url,
                   'linkedin_url': blog_config.linkedin_url,
                   'user': None}

    def generate(self, template_name, template_values={}):
        """Supplies a common template generation function.
           generate() augments the template variables.
        """
        side_bar_data = {'tag_list': blog_util.generate_tag_list(),
                         'archive_list': blog_util.generate_archive_list()}
        self.blog_values.update(template_values)
        self.blog_values.update(side_bar_data)
        self.response.out.write(blog_util.generate_template(template_name,
                                                            **self.blog_values)
                                                            )

    def set_secure_cookie(self, name, value):
        hashed_val = blog_util.make_secure_val(value)
        cookie_value = '{name}={value}; Path=/'.format(name=name,
                                                       value=hashed_val)
        self.response.headers.add_header('Set-Cookie', cookie_value)

    def remove_secure_cookie(self, name):
        self.response.headers.add_header('Set-Cookie',
                                         '{name}=; Path=/'.format(name=name))

    def check_secure_cookie(self):
        try:
            user_id_cookie_val = self.request.cookies.get('user_id')
            return blog_util.check_secure_val(user_id_cookie_val)
        except AttributeError:
            return None

    def check_admin_status(self):
        """User var. is used to generate Admin dropdown menu in base.html"""
        if self.check_secure_cookie():
            self.blog_values['user'] = 'admin'

    def check_if_admin(self, template):
        if not self.check_secure_cookie():
            self.redirect('/blog')
            return
        else:
            self.blog_values['user'] = 'admin'
            self.generate(template, {})

    def post_eval(self, preview, update, **params):
        if params:
            self.redirect(blog_util.post_helper(params['subject'],
                                                params['content'],
                                                params['image_url'],
                                                params['tag'],
                                                preview,
                                                update))
            return
        else:
            params.update({'newpost_error': 'All fields  are required!'})
            self.generate('newpost.html', **params)


class BlogPostHandler(BaseRequestHandler):
    """Main Blog Page Handler"""
    def get(self):
        blog_entries = blog_util.main_page_posts()
        self.check_admin_status()
        self.generate('blog.html', {'blog_entries': blog_entries})


class PermalinkHandler(BaseRequestHandler):
    def get(self, post_id):
        """Generator of permalink page for each blog entry
           postid variable gets passed in (i.e. /blog/(\d+))
        """
        post_num = int(post_id)
        blog_post = blog_models.BlogPost.get_by_id(post_num)
        logging.error('DB write: Permalink Visit')
        blog_post.visits += 1
        blog_post.put()

        self.check_admin_status()
        if not blog_post:
            self.generate('error.html', {})
        else:
            self.generate('blogpost.html',
                          {'blog_post': blog_post,
                           'blog_author_link': blog_config.blog_author_link})


class TagHandler(BaseRequestHandler):
    """Tag Page Handler"""
    def get(self, tag_name):
        tag_list = dict(blog_util.generate_tag_list())
        self.check_admin_status()
        if tag_name not in tag_list.keys():
            self.redirect('/blog')
            return
        else:
            blog_entries = blog_util.tag_cache(tag_name)
            self.generate('blog.html', {'blog_entries': blog_entries})


class ArchiveHandler(BaseRequestHandler):
    """Archive Page Handler"""
    def get(self, archive_year):
        archive_list = dict(blog_util.generate_archive_list())
        self.check_admin_status()
        if archive_year not in archive_list.keys():
            self.redirect('/blog')
            return
        else:
            blog_entries = blog_util.archive_cache(archive_year)
            self.generate('blog.html', {'blog_entries': blog_entries})


class NewPostHandler(BaseRequestHandler):
    """Generages and Handles New Blog Post Entires."""
    def get(self):
        if self.check_secure_cookie():
            self.blog_values['user'] = 'admin'
            self.generate('newpost.html', {})
        else:
            self.redirect('/blog/login')
            return

    def post(self):
        update = None
        preview = self.request.POST.get('Preview', None)
        params = blog_util.blog_post_param(self.request)
        self.post_eval(preview, update, **params)


class PreviewHandler(BaseRequestHandler):
    """Blog Post Preview Handler"""
    def get(self):
        post_key = db.Key.from_path('PostPreview', 'preview')
        blog_post = blog_models.PostPreview.get(post_key)

        self.check_admin_status()
        if not blog_post:
            self.generate('error.html', {})
        else:
            self.generate('preview.html', {'preview': blog_post})


class EditPostHandler(BaseRequestHandler):
    """Handler to Edit Blog Post Entries"""
    def get(self):
        if self.check_secure_cookie():
            self.blog_values['user'] = 'admin'
            post_id = int(self.request.get('q'))
            blog_post = blog_models.BlogPost.get_by_id(post_id)
            self.generate('newpost.html',
                          {'subject': blog_post.subject,
                           'content': blog_post.content,
                           'image_url': blog_post.image_url,
                           'tag': blog_post.tag})
        else:
            self.redirect('/blog/login')
            return

    def post(self):
        update = int(self.request.get('q'))
        preview = self.request.POST.get('Preview', None)
        params = blog_util.blog_post_param(self.request)
        self.post_eval(preview, update, **params)


class LoginHandler(BaseRequestHandler):
    """Admin Login Page Handler"""
    def get(self):
        if self.check_secure_cookie():
            self.redirect('/blog')
            return
        else:
            self.generate('login.html', {})

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        user = blog_models.Admin.login_validation(username)

        if user and blog_util.valid_pw(username, password, user.admin_pw_hash):
            # If statement below prevents default error message on /blog/login
            if blog_util.valid_pw(username, password, user.admin_pw_hash):
                # var added to 'admin' to provide unique cookie for each login
                var = blog_util.random_letters()
                self.set_secure_cookie('user_id', 'admin' + var)
                self.redirect('/blog/admin-pref')
                return
        else:
            self.generate('login.html',
                          {'error_login': 'Invalid Username and/or Password'})


class LogoutHandler(BaseRequestHandler):
    """Logout Handler"""
    def get(self):
        self.remove_secure_cookie('user_id')
        self.blog_values['user'] = None
        self.redirect('/blog')
        return


class AboutHandler(BaseRequestHandler):
    """About Page Handler"""
    def get(self):
        self.check_admin_status()
        self.generate('about.html', {})


class ContactHandler(BaseRequestHandler):
    """Contact Page Handler"""
    def get(self):
        self.check_admin_status()
        self.generate('contact.html', {})

    def post(self):
        email_user = cgi.escape(self.request.get('email_from'))
        email_subject = cgi.escape(self.request.get('email_subject'))
        email_message = cgi.escape(self.request.get('email_message'))
        message = blog_util.send_mail(email_user, email_subject, email_message)
        self.generate('contact.html', {'message': message})


class AdminPrefHandler(BaseRequestHandler):
    """Admin Preferences Page Handler"""
    def get(self):
        self.check_if_admin('admin-pref.html')


class UsernameChangeHandler(BaseRequestHandler):
    """Change Username Page Handler"""
    def get(self):
        self.check_if_admin('username-change.html')

    def post(self):
        new_username = self.request.get('new_username')
        pw = self.request.get('password')
        message = blog_models.Admin.change_username(new_username, pw)
        self.generate('username-change.html',
                      {'message_change_username': message})


class PasswordChangeHandler(BaseRequestHandler):
    def get(self):
        self.check_if_admin('pw-change.html')

    def post(self):
        password = self.request.get('password')
        verify_password = self.request.get('verify_password')
        message = blog_models.Admin.change_password(password,
                                                    verify_password)
        self.generate('pw-change.html',
                      {'message_change_pw': message})


class PostHistoryHandler(BaseRequestHandler):
    """Post History Handler"""
    def get(self):
        self.check_admin_status()
        blog_entries = blog_util.visits_cache()
        self.generate('post-history.html', {'blog_entries': blog_entries})


class AdminHandler(BaseRequestHandler):
    #FOR TESTING PURPOSES ONLY
    def get(self):
        pw_hash = blog_util.make_pw_hash(blog_config.admin_username,
                                         blog_config.admin_pw)
        admin = blog_models.Admin(admin_username=blog_config.admin_username,
                                  admin_pw_hash=pw_hash,
                                  key_name='admin_key_name')
        admin.put()
        self.redirect('/blog')
        return
