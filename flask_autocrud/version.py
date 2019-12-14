__version_info__ = (2, 1, 0)
__version__ = '.'.join(map(str, __version_info__))

__author_info__ = {
    'name': 'cs91chris',
    'email': 'cs91chris@voidbrain.me'
}

__author__ = "{} <{}>".format(
    __author_info__['name'],
    __author_info__['email']
)

__all__ = [
    '__version__',
    '__version_info__',
    '__author__',
    '__author_info__'
]
