import os

import webapp2

import handlers
import util


routes = [('/', handlers.BlogPostHandler),
          ('/blog/newpost', handlers.NewPostHandler),
          ('/blog/newpost/preview', handlers.PreviewHandler),
          ('/blog/about', handlers.AboutHandler),
          ('/blog/contact', handlers.ContactHandler),
          ('/blog/login', handlers.LoginHandler),
          ('/blog/logout', handlers.LogoutHandler),
          ('/blog/admin', handlers.AdminHandler),
          ('/blog/admin-pref', handlers.AdminPrefHandler),
          ('/blog/pwchange', handlers.PasswordChangeHandler),
          ('/blog/userchange', handlers.UsernameChangeHandler),
          ('/blog/post-history', handlers.PostHistoryHandler),
          ('/blog/post-change', handlers.EditPostHandler),
          ('/blog/(\d+)', handlers.PermalinkHandler),
          ('/blog/tags/(.*)', handlers.TagHandler),
          ('/blog/archive/(\d{4})', handlers.ArchiveHandler)]

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication(routes, debug=debug)

app.error_handlers[404] = util.handle_error
if not app.debug:
    app.error_handlers[500] = util.handle_error
