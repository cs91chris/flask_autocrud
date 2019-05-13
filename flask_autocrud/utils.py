from .config import HttpStatus as status


def links_header(resource):
    """

    :param resource:
    :return:
    """
    links = resource.links()
    link_string = '<{}>; rel=self'.format(links['self'])

    for k, l in links.items():
        if k != 'self':
            link_string += ', <{}>; rel=related'.format(l)

    return {'Link': link_string}


def location_header(resource):
    """

    :param resource:
    :return:
    """
    location = resource.links()
    return {'Location': location['self']}


def pagination_headers(pagination):
    """

    :param pagination:
    :return:
    """
    code = status.SUCCESS

    total_results = pagination.total_results
    page_number = pagination.page_number
    num_pages = pagination.num_pages
    page_size = pagination.page_size

    if num_pages > 1 and total_results > page_size:
        code = status.PARTIAL_CONTENT

    if page_number == num_pages:
        code = status.SUCCESS

    return {
        'Pagination-Count': total_results,
        'Pagination-Page': page_number,
        'Pagination-Num-Pages': num_pages,
        'Pagination-Limit': page_size
    }, code
