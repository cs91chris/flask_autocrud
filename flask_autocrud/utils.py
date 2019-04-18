from datetime import datetime
from decimal import Decimal

from .model import Model


def from_model_to_dict(data):
    resp = {}

    for k, v in data.items():
        if k.startswith('_'):
            continue

        if isinstance(v, Model):
            resp.update({
                v.__class__.__name__: from_model_to_dict(v.__dict__)
            })
        elif isinstance(v, list):
            if len(v) > 0:
                name = v[0].__class__.__name__ + 'List'
                resp.update({
                    name: [from_model_to_dict(i.__dict__) for i in v]
                })
        else:
            if isinstance(v, Decimal):
                v = float(v)
            elif isinstance(v, datetime):
                v = v.isoformat()

            resp.update({k: v})
    return resp
