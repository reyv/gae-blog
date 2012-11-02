import os
import webapp2
import blog_handlers
import blog_util


routes = [('/blog/?', blog_handlers.BlogPostHandler),
            ('/blog/newpost', blog_handlers.NewPostHandler),
            ('/blog/newpost/preview', blog_handlers.PreviewHandler),
            ('/blog/about', blog_handlers.AboutHandler),
            ('/blog/contact', blog_handlers.ContactHandler),
            ('/blog/login', blog_handlers.LoginHandler),
            ('/blog/logout', blog_handlers.LogoutHandler),
            ('/blog/admin', blog_handlers.AdminHandler),
            ('/blog/admin-pref', blog_handlers.AdminPrefHandler),
            ('/blog/pwchange', blog_handlers.PasswordChangeHandler),
            ('/blog/userchange', blog_handlers.UsernameChangeHandler),
            ('/blog/post-history', blog_handlers.PostHistoryHandler),
            ('/blog/(\d+)', blog_handlers.PermalinkHandler),
            ('/blog/tags/(.*)', blog_handlers.TagHandler),
            ('/blog/archive/(\d{4})', blog_handlers.ArchiveHandler)]

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication(routes, debug=debug)

app.error_handlers[404] = blog_util.handle_error
if not app.debug:
    app.error_handlers[500] = blog_util.handle_error
