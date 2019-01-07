import io
import csv

from flask import abort
from flask import request
from flask import Response
from flask import make_response

from flask_json import as_json


def get_json():
    """

    :return:
    """
    req = request.get_json()
    if not req:
        abort(400, 'No JSON given')
    return req


def no_content():
    """

    :return:
    """
    resp = make_response('', 204)
    del resp.headers['Content-Type']
    del resp.headers['Content-Length']
    return resp


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
        output
        ,data[0].keys()
        ,dialect='excel-tab'
        ,delimiter=delimiter
        ,quotechar=qc, quoting=q
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
            'Content-Disposition': 'attachment; filename=%s.csv' % (filename,)
        }
    )


@as_json
def resp_json(data, root=None):
    """

    :param data:
    :param root:
    :return:
    """
    if root is not None:
        return {
            str(root): data
        }
    else:
        return data


@as_json
def response_with_links(resource, code=200):
    """

    :param resource:
    :param code:
    :return:
    """
    links = resource.links()
    link_string = '<{}>; rel=self'.format(links['self'])

    for link in links.values():
        link_string += ', <{}>; rel=related'.format(link)

    return resource.to_dict(), code, {'Link': link_string}
