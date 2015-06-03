from django.contrib.sites.models import get_current_site, Site
from django.core.urlresolvers import resolve, Resolver404
from django.http import (
    HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponseGone)

from .models import Redirect
from .utils import get_redirect_patterns, replace_partial_url


class RedirectMiddleware(object):
    """
        Process the redirect patterns from redirects.dynamic_urls.
    """

    def try_resolve(self, path, request):
        urlconf = get_redirect_patterns(request)
        redirect, args, kwargs = resolve(path, urlconf=urlconf)
        return redirect(request, **kwargs)

    def process_response(self, request, response):
        current_site = get_current_site(request)
        site = Site.objects.get(id=3)

        if response.status_code != 404 and current_site.domain != site.domain:
            # No need to check for a redirect for non-404 responses.
            return response

        path = request.get_full_path()

        # No regex redirect was found try a simple replace
        db_filters = {
            'status': 1,
            'site': current_site,
            'is_partial': False,
            'uses_regex': False
        }

        redirects = Redirect.objects.filter(**db_filters)

        for redirect in redirects:
            from_url = redirect.from_url
            check_path = path

            # Strip leading slashes
            if from_url.startswith('/'):
                from_url = from_url[1:]

            if path.startswith('/'):
                check_path = path[1:]

            # Strip trailing slashes
            if from_url.endswith('/'):
                from_url = from_url[:-1]

            if check_path.endswith('/'):
                check_path = check_path[:-1]

            if redirect.from_url == '/about/our-blog/how-nation-launch-it-rocket/':
                print "from_url", from_url
                print "check_path", check_path

            if from_url.lower() == check_path.lower():
                if redirect.to_url == '':
                    return HttpResponseGone()

                if redirect.http_status == 301:
                    return HttpResponsePermanentRedirect(redirect.to_url)
                elif redirect.http_status == 302:
                    return HttpResponseRedirect(redirect.to_url)

        # Check URLs that have regex match
        try:
            return self.try_resolve(path, request)
        except Resolver404:
            pass

        # Try again by changing the slash
        try:
            # if not, check if adding/removing the trailing slash helps
            if path.endswith('/'):
                new_path = path[:-1]
            else:
                new_path = path + '/'

            return self.try_resolve(new_path, request)
        except Resolver404:
            pass

        # Try looking for a partial
        db_filters = {
            'status': 1,
            'site': current_site,
            'is_partial': True
        }

        redirects = Redirect.objects.filter(**db_filters)

        for redirect in redirects:
            if redirect.from_url in path:
                if redirect.to_url == '':
                    return HttpResponseGone()

                # Do a replace on the url and do a redirect
                path = replace_partial_url(
                    path, redirect.from_url, redirect.to_url)

                if redirect.http_status == 301:
                    return HttpResponsePermanentRedirect(path)
                elif redirect.http_status == 302:
                    return HttpResponseRedirect(path)

        return response
