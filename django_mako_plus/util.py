from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import base64, os, os.path


# this is populated with the dictionary of options in engine.py when
# Django initializes the template engine
DMP_OPTIONS = {}

# the key for the DMP singleton engine instance (stored in DMP_OPTIONS by engine.py)
DMP_INSTANCE_KEY = 'django_mako_plus_instance'

# set up the logger
import logging
log = logging.getLogger('django_mako_plus')

################################################################
###   DMP instance and apps

def get_dmp_instance():
    '''
    Retrieves the DMP template engine instance.
    '''
    try:
        return DMP_OPTIONS[DMP_INSTANCE_KEY]
    except KeyError:
        raise ImproperlyConfigured('The Django Mako Plus template engine did not initialize correctly.  Check your logs for previous errors that may have caused initialization to fail, and check that DMP is set correctly in settings.py.')


def get_dmp_app_configs():
    '''
    Gets the DMP-enabled app configs, which will be a subset of all installed apps.  This is a generator function.
    This method does not use the registry cache.  Instead, it looks through all Django apps in settings.py and
    yields any with "DJANGO_MAKO_PLUS = True" in its __init__.py.
    '''
    for config in apps.get_app_configs():
        # check for the DJANGO_MAKO_PLUS = True in the app (should be in app/__init__.py)
        if getattr(config.module, 'DJANGO_MAKO_PLUS', False):
            yield config



################################################################
###   Special type of list used for url params

class URLParamList(list):
    '''
    A simple extension to Python's list that returns '' for indices that don't exist.
    For example, if the object is ['a', 'b'] and you call obj[5], it will return ''
    rather than throwing an IndexError.  This makes dealing with url parameters
    simpler since you don't have to check the length of the list.
    '''
    def __getitem__(self, idx):
        '''Returns the element at idx, or '' if idx is beyond the length of the list'''
        return self.get(idx, '')

    def get(self, idx, default=''):
        '''Returns the element at idx, or default if idx is beyond the length of the list'''
        # if the index is beyond the length of the list, return ''
        if isinstance(idx, int) and (idx >= len(self) or idx < -1 * len(self)):
            return default
        # else do the regular list function (for int, slice types, etc.)
        return super().__getitem__(idx)


##########################################
###   Utilities

def merge_dicts(*dicts):
    '''
    Merges an arbitrary number of dicts, starting 
    with the first argument and updating through the
    last argument (last dict wins on conflicting keys).
    '''
    merged = {}
    for d in dicts:
        merged.update(d)
    return merged
    
 

def split_app(path):
    '''
    Splits a path on the app, returning (app config, relative path within app).
    
    This function uses os.path.samefile to split even if a path is specified differently.
    The drawback is significantly reduced speed because of a double loop, so use with care.
    '''
    configs = list(get_dmp_app_configs())  # cache the generator results so we can go through it several times
    def get_config(app_dir):
        if os.path.exists(app_dir):
            for config in configs:
                if os.path.samefile(config.path, app_dir):
                    return config
        return None
    parts = os.path.normpath(path).split(os.path.sep)
    for i in range(len(parts), 0, -1):
        app_config = get_config(os.path.sep.join(parts[:i]))
        if app_config is not None:
            return app_config, os.path.sep.join(parts[i:])
    return None, path
        
        
    


