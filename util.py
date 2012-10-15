import hashlib
import hmac
import config
import random
import logging

from string import letters
from google.appengine.api import memcache
from google.appengine.ext import db


#Hasning functions - cookies


def hash_str(s):

    return hmac.new(config.cookie_secret, s).hexdigest()


def make_secure_val(s):

    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):

    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

#Hashing functions - user


def make_salt(length=config.salt_length):

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
        posts = db.GqlQuery("""
                                SELECT *
                                FROM BlogPost
                                ORDER BY created
                                DESC
                                LIMIT 10
                            """)
        memcache.set(key, posts)
    return posts


def tag_cache(tag_name, update=False):
    key = 'tag_%s' % tag_name
    tag = memcache.get(key)
    if tag is None or update:
        logging.error('DB Query: Tag')
        tag = db.GqlQuery("""
                                SELECT *
                                FROM BlogPost
                                WHERE tag='%s'
                            """
                            % tag_name)
        memcache.set(key, tag)
    return tag