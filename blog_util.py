import os
import re
import hashlib
import hmac
import random
import logging
from string import letters
from collections import Counter

import jinja2
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import mail

import blog_config
import blog_models


#Template variables


def generate_template(template_name, **kwargs):
    """Template generation helper function"""
    path = os.path.join(os.path.dirname(__file__), 'static/html/blog')
    j_loader = jinja2.Environment(loader=jinja2.FileSystemLoader(path),
                                  autoescape=False)
    jinja_environment = j_loader
    template = jinja_environment.get_template(template_name)
    return template.render(**kwargs)


#Hasning functions - cookies


def random_letters():
    """Generates random letters for cookie name to provide unique
       name for each login.
    """
    return ''.join(random.choice(letters) for x in blog_config.cookie_secret)


def hash_str(s):
    """Hashing of cookies for Admin login."""
    return hmac.new(blog_config.cookie_secret, s).hexdigest()


def make_secure_val(s):
    """Makes a secure hash in the form of name | hashed value"""
    return "{s}|{hash}".format(s=s, hash=hash_str(s))


def check_secure_val(h):
    """Checkes to make sure that cookies are valid for accessing Admin pref"""
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

#Hashing functions - user


def make_salt(length=blog_config.salt_length):
    """Makes a salt for passwords that is stored in the db"""
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(username, password, salt=None):
    """Hashes the password to include the salt, which is stored in the db"""
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    return '{salt},{h}'.format(salt=salt, h=h)


def valid_pw(username, password, h):
    """Checks to see if pasword is valid based on the stored hash"""
    salt = h.split(',')[0]
    return h == make_pw_hash(username, password, salt)

# Memcache Functions


def main_page_posts(update=False):
    """Caching for top 10 posts shown in the Blog Main Page"""
    key = 'main_page_posts'
    posts = memcache.get(key)
    if posts is None or update:
        logging.error('DB Query: Main Page')
        posts = db.GqlQuery("""SELECT *
                            FROM BlogPost
                            ORDER BY created
                            DESC
                            LIMIT 10
                            """)
        memcache.set(key, posts)
    return posts


def tag_cache(tag_name, update=False):
    """Stores cache for all tags to be displayed on every Blog Page"""
    key = 'tag_{tag}'.format(tag=tag_name)
    tag = memcache.get(key)
    if tag is None or update:
        logging.error('DB Query: Tag')
        tag = db.GqlQuery(""" SELECT * FROM BlogPost
                              WHERE tag = :1""", tag_name)
        memcache.set(key, tag)
    return tag


def archive_cache(archive_year, update=False):
    """Stores cache for all archive years to be displayed on every Blog page"""
    next_year = str(int(archive_year) + 1)
    first_year = '{year}-1-1'.format(year=archive_year)
    second_year = '{year}-1-1'.format(year=next_year)

    key = 'archive_{year}'.format(year=archive_year)
    year = memcache.get(key)
    if year is None or update:
        logging.error('DB Query: Archive')
        year = db.GqlQuery("""SELECT * FROM BlogPost
                                WHERE created >= DATE(:first)
                                AND created < DATE(:second)
                           """, first=first_year, second=second_year)
        memcache.set(key, year)
    return year


def visits_cache(update=False):
    """Stores cache of the Number of visits to be displayed in Admin pref."""
    key = 'visits_cache'
    posts = memcache.get(key)
    if posts is None or update:
        logging.error('DB Query: Visits Sorting DESC')
        posts = db.GqlQuery("""SELECT *
                            FROM BlogPost
                            ORDER BY visits DESC
                            """)
        memcache.set(key, posts)
    return posts

#Misc. Functions


def generate_tag_list():
    """Queries db for a unique list of tags sorted alphabetically"""
    tag_entries = db.GqlQuery("SELECT tag FROM BlogPost")
    tags_all = [str(item.tag) for item in tag_entries]  # excecute query
    c = Counter(tags_all)    # provides dict with count of each tag
    return sorted(c.iteritems())  # returns list w/ tuples in alpha. order


def generate_archive_list():
    """Queries db for a unique list of archive years sorted desc"""
    archive = db.GqlQuery("""   SELECT *
                                FROM BlogPost
                                WHERE created>DATE('2009-1-1')
                          """)
    # excecute query
    archive_years = [str(item.created.strftime('%Y')) for item in archive]
    c = Counter(archive_years)    # provides dict with count of each year
    return sorted(c.iteritems())  # returns list w/ ordered tuples


#Contact for functions


def send_mail(email, email_subject, email_message):
    """Send mail function"""
    match = re.match(r'\w+\.?\w+@\w+\.\w{2,3}', email)
    if match:
        message = mail.EmailMessage(sender=blog_config.email_from,
                                    subject=email_subject)
        message.to = blog_config.email_to
        message.html = email_message + '<br /><br /> The sender is ' + email
        message.send()
        e = blog_models.SubscribeEmail(email=email)
        e.put()
        return 'Thank you for contacting us.'
    else:
        return 'You have input an invalid entry. Please retry.'

# URL Exception Handling


def handle_error(request, response, exception):
    """Handles errors for URL requests that are not handled by server"""
    status_code = exception.status_int or 500
    logging.exception(exception)
    var = {'status_code': status_code}
    response.write(generate_template('error.html', **var))
    response.set_status(status_code)

# New Post Functions


def post_helper(subject, content, tag, image_url, preview, update=None):
    """Helper function for NewPost Handler"""
    if preview:
        return post_preview(subject, content, tag, image_url)

    elif update:
        return post_update(subject, content, tag, image_url, update)
    else:
        return post_new(subject, content, tag, image_url)


def blog_post_param(request):
    subject = request.get('subject')
    content = request.get('content')
    content = content.replace('\n', '<br>')
    image_url = request.get('image_url')
    tag = request.get('tag')
    if subject and content and image_url and tag:
        return {'subject': subject,
                'content': content,
                'image_url': image_url,
                'tag': tag}


def post_preview(subject, content, image_url, tag):
    """Creates a Preview Entity of the kind PostPreview
       and stores in into the db.
    """
    preview = blog_models.PostPreview(subject=subject,
                                          content=content,
                                          image_url=image_url,
                                          tag=tag,
                                          key_name='preview')
    preview.put()
    return '/blog/newpost/preview'


def post_update(subject, content, image_url, tag, update):
    """Helper function to fetch an existing post and
       modifies it's contents.
    """
    blog_post = blog_models.BlogPost.get_by_id(update)
    blog_post.subject = subject
    blog_post.content = content
    blog_post.tag = tag
    blog_post.image_url = image_url
    blog_post.put()
    return '/blog/{post_id}'.format(post_id=update)


def post_new(subject, content, image_url, tag):
    """Helper function that creates a new Entity for
       a new blog post.
    """
    blog_entry = blog_models.BlogPost(subject=subject,
                                      content=content,
                                      image_url=image_url,
                                      tag=tag)
    blog_entry.put()
    post_id = str(blog_entry.key().id())
    blog_entry.post_id = post_id
    blog_entry.put()

    #rerun query and update the cache.
    main_page_posts(True)
    tag_cache(tag, True)
    archive_year = blog_entry.created.strftime('%Y')
    archive_cache(archive_year, True)
    visits_cache(True)
    return '/blog/{post_id}'.format(post_id=post_id)
