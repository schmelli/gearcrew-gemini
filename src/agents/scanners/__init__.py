"""
Scanner agents for the Gear-heads discovery team
"""
from .youtube_scanner import create_youtube_scanner
from .website_scanner import create_website_scanner
from .blog_scanner import create_blog_scanner
from .reddit_scanner import create_reddit_scanner

def create_scanner_agents():
    """Create all scanner agents"""
    return [
        create_youtube_scanner(),
        create_website_scanner(),
        create_blog_scanner(),
        create_reddit_scanner(),
    ]

__all__ = [
    'create_youtube_scanner',
    'create_website_scanner',
    'create_blog_scanner',
    'create_reddit_scanner',
    'create_scanner_agents',
]
