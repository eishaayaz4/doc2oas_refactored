'''
Configuration values
'''

import os

def env_or_false(key):
    '''
    Lookup environment key, returns False is not present
    '''
    try:
        return os.environ[key]
    except KeyError:
        return False

VERSION = "0.0.5"

SECRET = env_or_false("DOC2OASIE_SECRET") or 'super_secret_key'

LAST_COMMIT = env_or_false("LAST_COMMIT")

REPO_URL = "https://forge.etsi.org/rep/cti/doc2oas/tree/"