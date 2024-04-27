from flask import Flask, render_template, request, redirect, make_response
import string
import secrets

app = Flask(__name__)


def _generate_session_id_(length=50):
    """
    Generates a random string of fixed length
    :param length: 50
    :return: a random string of fixed length for session_id
    """
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@app.route('/', methods=['GET'])
def _index_services_():
    session_id = request.cookies.get('session_id')
    if session_id is None:
        session_id = _generate_session_id_()
        