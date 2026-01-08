"""
Cirkelline User Context Helpers
================================
Thread-local storage for user context during request handling.
"""

import threading

# Thread-local storage for user context
_request_context = threading.local()

def set_request_user_context(user_id: str, user_type: str):
    """Store user context for the current request thread"""
    _request_context.user_id = user_id
    _request_context.user_type = user_type

def get_request_user_context():
    """Retrieve user context for the current request thread"""
    return {
        'user_id': getattr(_request_context, 'user_id', None),
        'user_type': getattr(_request_context, 'user_type', 'Regular')
    }
