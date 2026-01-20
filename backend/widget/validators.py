from fnmatch import fnmatch
from urllib.parse import urlparse

def validate_origin(origin, allowed_domains):
    """Validate origin against allowed domains with wildcard support."""
    if not allowed_domains:
        return False

    parsed = urlparse(origin)
    domain = parsed.netloc

    # Handle port numbers if present
    if ':' in domain:
        domain = domain.split(':')[0]

    for allowed in allowed_domains:
        if domain == allowed or ('*' in allowed and fnmatch(domain, allowed.replace('*', '.*'))):
            return True
    return False
