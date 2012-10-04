import hashlib, hmac, config, random
from string import letters

#Hasning functions - cookies
def hash_str(s):
    return hmac.new(config.cookie_secret,s).hexdigest()

def make_secure_val(s):
    return "%s|%s" %(s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val
    
#Hashing functions - user
def make_salt(length = config.salt_length):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(username, password, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(username, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(username, password, salt)
