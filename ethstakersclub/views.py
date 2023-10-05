from django.views.decorators.http import require_GET
from django.http import HttpResponse
from django.shortcuts import reverse


@require_GET
def custom_robots_txt(request):
    # Get the full URL for the sitemap
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))

    # Build the robots.txt content with the full URL for the sitemap
    robots_txt = f"User-agent: *\nDisallow: /admin/\nDisallow: /user/signup/\nDisallow: /user/login/\n\nSitemap: {sitemap_url}"

    # Create an HTTP response with the robots.txt content
    response = HttpResponse(robots_txt, content_type='text/plain')
    return response