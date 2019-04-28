import io
import csv

from flask import Response
from flask import make_response

from flask_json import as_json

from .config import HTTP_STATUS
from .model import Model


def list_to_csv(data: list, delimiter=';', quoting=True, qc='"'):
    """

    :param data:
    :param delimiter:
    :param quoting:
    :param qc:
    :return:
    """
    q = csv.QUOTE_ALL if quoting else csv.QUOTE_NONE
    output = io.StringIO()

    w = csv.DictWriter(
        output,
        data[0].keys() if data else '',
        dialect='excel-tab',
        delimiter=delimiter,
        quotechar=qc,
        quoting=q
    )
    w.writeheader()
    w.writerows(data)

    return output.getvalue()


def resp_csv(data_list, filename):
    """

    :param data_list:
    :param filename:
    :return:
    """
    return Response(
        list_to_csv(data_list),
        mimetype='text/csv',
        headers={
            'Content-Type': 'text/csv',
            'Total-Count': len(data_list),
            'Content-Disposition': 'attachment; filename=%s.csv' % (filename,)
        }
    )


@as_json
def resp_json(data, root=None, code=HTTP_STATUS.SUCCESS):
    """

    :param data:
    :param root:
    :param code:
    :return:
    """
    if root is not None:
        return {
            str(root): data
        }, code
    else:
        return data, code


@as_json
def response_with_links(resource, code=HTTP_STATUS.SUCCESS):
    """

    :param resource:
    :param code:
    :return:
    """
    links = resource.links()
    link_string = '<{}>; rel=self'.format(links['self'])

    for link in links.values():
        link_string += ', <{}>; rel=related'.format(link)

    return resource.to_dict(), code, {
        'Link': link_string
    }


@as_json
def response_with_location(resource, code=HTTP_STATUS.CREATED):
    """

    :param resource:
    :param code:
    :return:
    """
    location = resource.links()

    return resource.to_dict(), code, {
        'Location': location['self']
    }


def no_content():
    """

    :return:
    """
    resp = make_response('', HTTP_STATUS.NO_CONTENT)
    del resp.headers['Content-Type']
    del resp.headers['Content-Length']
    return resp


@as_json
def response_with_pagination(resource, pagination):
    """

    :param resource:
    :param pagination:
    :return:
    """
    code = HTTP_STATUS.SUCCESS

    total_results = pagination.total_results
    page_number = pagination.page_number
    num_pages = pagination.num_pages
    page_size = pagination.page_size

    if num_pages > 1 and total_results > page_size:
        code = HTTP_STATUS.PARTIAL_CONTENT

    if page_number == num_pages:
        code = HTTP_STATUS.SUCCESS

    if isinstance(resource, Model):
        resource = resource.to_dict()

    return resource, code, {
        'Pagination-Count': total_results,
        'Pagination-Page': page_number,
        'Pagination-Num-Pages': num_pages,
        'Pagination-Limit': page_size
    }
