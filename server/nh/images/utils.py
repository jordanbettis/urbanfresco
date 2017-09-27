import math, json

def wilson_score(v, n):
    """
    Given lower lower bound of the wilson score interval.
    
    The return value will be in the range (0, 1) where a higher
    proportion of upvotes will yield a number closer to 1.

    The purpose is to sort items by binomal mean but favoring
    items with more votes.
    """
    if n == 0:
        return 0
    phat = float(v)/float(n)
    z = 1.6 ## p=.95 
    z2 = z**2
    n2 = n**2
    return (
        (phat + z2/(2*n) - z * math.sqrt( (phat*(1-phat))/n + z2/(4*n2) ))
        / (1+z2/n))

def make_json_info(image, session):
    """
    Create a json formatted info file suitable for sending to the
    client, given an Image or an Image.info object, or an iterable
    containing them.
    """
    if hasattr(image, "info"):
        image_info = image.info(session)
    else:
        image_info = image

    if "id" in image_info:
        del image_info['id']

    return json.dumps(image_info)
