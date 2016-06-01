from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
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

        if response.status_code != 404 and current_site.id not in settings.SITES_TO_REDIRECT:
            # No need to check for a redirect for non-404 responses.
            return response

        path = request.get_full_path()

        original = path

        add_trailing = path + '/'

        no_trailing = path
        # Strip trailing slashes
        if no_trailing.endswith('/'):
            no_trailing = path[:-1]

        no_leading = path
        if no_leading.startswith('/'):
            no_leading = path[1:]

        has_no_trailing = ''
        # If it has a trailing slash remove it
        if path.endswith('/'):
            has_no_trailing = path[:-1]
        # If we took a slash off remember that or if not just use the original
        has_no_trailing = has_no_trailing or path
        # If it has leading slash remove it
        if has_no_trailing.startswith('/'):
            no_slashes_at_all = has_no_trailing[1:]
        # If we took a slash off remember that or if not just use the result of
        # the trailing removale
        no_slashes_at_all = no_slashes_at_all or has_no_trailing

        url_options = [original, no_trailing, no_leading, no_slashes_at_all, add_trailing]

        db_filters = {
            'status': 1,
            'site': current_site,
            'is_partial': False,
            'uses_regex': False,
            'from_url__in': url_options
        }

        # Try a replace
        try:
            redirect = Redirect.objects.get(**db_filters)

            if redirect.http_status == 301:
                return HttpResponsePermanentRedirect(redirect.to_url)
            elif redirect.http_status == 302:
                return HttpResponseRedirect(redirect.to_url)
        except Redirect.DoesNotExist:
            pass

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
