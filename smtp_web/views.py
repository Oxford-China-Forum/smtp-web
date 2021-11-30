import os
import time

from flask import current_app as app
from flask import request, session, render_template, redirect, url_for

from .smtp_utils import *


@app.route('/', methods=['GET'])
def index_page():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def upload_files():
    if 'body' not in request.files or 'recipients' not in request.files:
        return 'bad'
    # Reformat filenames and save files
    body_file = request.files['body']
    recipients_file = request.files['recipients']
    body_extension = '-body' + get_file_extension(body_file.filename)
    recipients_extension = '-recipients' + get_file_extension(recipients_file.filename)
    current_time = time.strftime('%Y%m%d-%H%M%S')
    body_path = os.path.join(app.config['UPLOAD_DIR'], current_time + body_extension)
    recipients_path = os.path.join(app.config['UPLOAD_DIR'], current_time + recipients_extension)
    body_file.save(body_path)
    recipients_file.save(recipients_path)

    body = get_message_body(body_path)
    recipients = get_recipients(recipients_path)
    session['body'] = body
    session['recipients'] = vars(recipients[0])
    print(session['recipients'])
    session['ready'] = True
    return 'good'


@app.route('/preview', methods=['GET'])
def get_email_preview():
    print(session.get('ready'))
    assert session.get('ready')
    return generate_preview(session['body'], session['recipients'])


def get_file_extension(filename):
    if '.' not in filename:
        return ''
    return '.' + filename.rsplit('.', 1)[1].lower()
