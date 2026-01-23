from fnmatch import fnmatch
from urllib.parse import urlparse

def validate_origin(origin, allowed_domains):
    """Validate origin against allowed domains with wildcard support."""
    if not allowed_domains:
        return False

    parsed = urlparse(origin)
    domain = parsed.netloc

    # Handle port numbers if present
    # Handle port numbers if present
    if ':' in domain:
        domain = domain.split(':')[0]

    # Always allow localhost for development convenience
    if domain in ['localhost', '127.0.0.1']:
        return True

    # If allowed_domains is empty, block everything else (except localhost above)
    if not allowed_domains:
        return False

    for allowed in allowed_domains:
        if domain == allowed or ('*' in allowed and fnmatch(domain, allowed.replace('*', '.*'))):
            return True
    return False
