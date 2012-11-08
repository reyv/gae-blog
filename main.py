import os

import webapp2

import handlers
import util


routes = [('/', handlers.BlogPostHandler),
          ('/newpost', handlers.NewPostHandler),
          ('/newpost/preview', handlers.PreviewHandler),
          ('/about', handlers.AboutHandler),
          ('/contact', handlers.ContactHandler),
          ('/login', handlers.LoginHandler),
          ('/logout', handlers.LogoutHandler),
          ('/admin', handlers.AdminHandler),
          ('/admin-pref', handlers.AdminPrefHandler),
          ('/pwchange', handlers.PasswordChangeHandler),
          ('/userchange', handlers.UsernameChangeHandler),
          ('/post-history', handlers.PostHistoryHandler),
          ('/post-change', handlers.EditPostHandler),
          ('/(\d+)', handlers.PermalinkHandler),
          ('/tags/(.*)', handlers.TagHandler),
          ('/archive/(\d{4})', handlers.ArchiveHandler)]


debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication(routes, debug=debug)

app.error_handlers[404] = util.handle_error404
if not app.debug:
    app.error_handlers[500] = util.handle_error500
