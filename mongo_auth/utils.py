import json, urllib

# TODO: Redo all this, it is not really used except on one place

def graph_api_url(fb_request, user=None, token=False):
    """ 
    Format Facebook Graph API URL. 
    """
    
    param = ''
    if user and token:
        param = '?access_token=%s' % user.facebook_access_token
    results = 'https://graph.facebook.com/%s/%s' % (fb_request, param)
    return results

def valid_token(user):
    """
    Check to see if a user's Facebook token is still valid.
    """

    data = json.load(urllib.urlopen(graph_api_url('me', user, token=True)))
    return 'error' not in data
