"""
Debug script to understand URL resolution for team endpoints.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver
from django.db import connection

def show_urls(urlpatterns, prefix=''):
    """Recursively show all URL patterns."""
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            # It's an include()
            new_prefix = prefix + str(pattern.pattern)
            show_urls(pattern.url_patterns, new_prefix)
        elif isinstance(pattern, URLPattern):
            # It's a path()
            full_path = prefix + str(pattern.pattern)
            if 'team' in full_path.lower():
                print(f"✅ {full_path}")
                if hasattr(pattern.callback, 'cls'):
                    print(f"   ViewSet: {pattern.callback.cls.__name__}")
                    print(f"   Actions: {pattern.callback.actions}")

print("=" * 60)
print("URLs REGISTRADAS COM 'TEAM'")
print("=" * 60)

# Get tenant URLconf
from config.urls import urlpatterns as tenant_urls
show_urls(tenant_urls)

print("\n" + "=" * 60)
print("TESTANDO RESOLUÇÃO DE URL")
print("=" * 60)

from django.urls import resolve
from django.test import RequestFactory

factory = RequestFactory()

# Test URL resolution
test_urls = [
    '/api/team/members/',
    '/api/team/invites/',
    '/api/team/members/1/',
]

for url in test_urls:
    try:
        match = resolve(url)
        print(f"\n✅ {url}")
        print(f"   View: {match.func}")
        print(f"   Name: {match.url_name}")
        print(f"   Namespace: {match.namespace}")
        if hasattr(match.func, 'cls'):
            print(f"   ViewSet: {match.func.cls.__name__}")
            print(f"   Actions: {match.func.actions}")
    except Exception as e:
        print(f"\n❌ {url}")
        print(f"   Error: {e}")
