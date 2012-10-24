Simple Blog for Google App Engine
=================================

This is a simple blog created with Python 2.7 to run on Google App Engine.

This blog was inspired from the CS253 course I took on Udacity.com. The blog has been greatly improved to
include optimized, efficient and practical code. I mainly created it as a learning experience for
web development and I also needed a blog for my own use.

This blog uses the following:

- Python 2.7
- Google App Engine
- Google's db 
- Google's Gql for queries
- HTML5 Boilerplate v4.0.0 (via the initializr.com)
- Titter Bootstrap v2.1.1 (via the initializr.com)
- Modernizer v2.6.1 (via the initializr.com)
- jQuery v1.8.1 (via the initializr.com)
- jinja2 templates (via Google App Engine)


Instructions
============

Once the app has been uploaded to your App Engine Account, do the following steps:

- Visit http://www.YOURDOMAINNAME.com/blog/admin to create an initial admin account.
- The default username and password in the config.py file is 'admin' and 'password', respectively.
- Visit the login section of the page and type in the default username and password.
- Visit the change username and change password sections of the site to create a unique username
   and a more secure password.
- Once this is complete, open the main.py file and delete the AdminHandler class towards the bottom.
- Delete '('/blog/admin', AdminHandler),' from the url routing list towards the bottom of the file.
- You are ready to use the blog.