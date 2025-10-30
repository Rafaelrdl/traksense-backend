"""
Script para verificar URLs registradas no Django
"""
from django.urls import get_resolver

def show_urls(urlpatterns=None, prefix=''):
    if urlpatterns is None:
        from django.conf import settings
        urlpatterns = __import__(settings.ROOT_URLCONF, {}, {}, ['']).urlpatterns
    
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            show_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            print(f"{prefix}{pattern.pattern}")

if __name__ == '__main__':
    print("URLs registradas:")
    print("=" * 80)
    show_urls()
