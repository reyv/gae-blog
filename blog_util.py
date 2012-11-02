import os
import jinja2
import re
import hashlib
import hmac
import random
import logging
import blog_config
import blog_models

from string import letters
from collections import Counter
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import mail


#Hasning functions - cookies


def hash_str(s):

    return hmac.new(blog_config.cookie_secret, s).hexdigest()


def make_secure_val(s):

    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):

    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

#Hashing functions - user


def make_salt(length=blog_config.salt_length):

    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(username, password, salt=None):

    if not salt:
        salt = make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(username, password, h):

    salt = h.split(',')[0]
    return h == make_pw_hash(username, password, salt)

# Memcache Functions


def main_page_posts(update=False):
    key = 'main_page_posts'
    posts = memcache.get(key)
    if posts is None or update:
        logging.error('DB Query: Main Page')
        posts = db.GqlQuery("""SELECT *
                            FROM BlogPost
                            ORDER BY created DESC LIMIT 10"""
                            )
        memcache.set(key, posts)
    return posts


def tag_cache(tag_name, update=False):
    key = 'tag_%s' % tag_name
    tag = memcache.get(key)
    if tag is None or update:
        logging.error('DB Query: Tag')
        tag = db.GqlQuery(""" SELECT * FROM BlogPost
                              WHERE tag = :1""", tag_name
                         )
        memcache.set(key, tag)
    return tag


def archive_cache(archive_year, update=False):
    next_year = str(int(archive_year) + 1)
    first_year = '%s-1-1' % archive_year
    second_year = '%s-1-1' % next_year

    key = 'archive_%s' % archive_year
    year = memcache.get(key)
    if year is None or update:
        logging.error('DB Query: Archive')
        year = db.GqlQuery("""SELECT * FROM BlogPost
                                WHERE created >= DATE(:first_year)
                                AND created < DATE(:second_year) """,
                                first_year=first_year,
                                second_year=second_year
                            )
        memcache.set(key, year)
    return year


def visits_cache(update=False):
    key = 'visits_cache'
    posts = memcache.get(key)
    if posts is None or update:
        logging.error('DB Query: Visits Sorting DESC')
        posts = db.GqlQuery("""SELECT *
                            FROM BlogPost
                            ORDER BY visits DESC"""
                            )
        memcache.set(key, posts)
    return posts

#Misc. Functions


def generate_tag_list():
    tag_entries = db.GqlQuery("SELECT tag FROM BlogPost")
    tags_all = [str(item.tag) for item in tag_entries]  # excecute query
    c = Counter(tags_all)    # provides dict with count of each tag
    return sorted(c.iteritems())  # returns list w/ tuples in alpha. order


def generate_archive_list():
    archive = db.GqlQuery("""   SELECT *
                                FROM BlogPost
                                WHERE created>DATE('2010-1-1')
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


def generate_template(template_name, **kwargs):
    path = os.path.join(os.path.dirname(__file__), 'static/html/blog')
    jinja_environment = jinja2.Environment(
                        loader=jinja2.FileSystemLoader(path),
                            autoescape=False)
    template = jinja_environment.get_template(template_name)
    return template.render(**kwargs)


def handle_error(request, response, exception):
    status_code = exception.status_int or 500
    logging.exception(exception)
    var = {'status_code': status_code}
    response.write(generate_template('error.html', **var))
    response.set_status(status_code)


#Template variables
