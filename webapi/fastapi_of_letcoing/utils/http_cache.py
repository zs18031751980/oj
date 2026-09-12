"""公开目录条件请求：每次重新确认可见性，再允许客户端复用摘要。"""
import hashlib

from flask import jsonify, request


def conditional_json(payload, headers=None):
    response = jsonify(payload)
    if headers:
        response.headers.update(headers)
    response.set_etag(hashlib.sha256(response.get_data()).hexdigest())
    response.headers['Cache-Control'] = 'private, no-cache'
    response.make_conditional(request)
    return response
