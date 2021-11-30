import os
import uuid
import time

from flask import current_app as app
from flask import request, session, render_template, jsonify, redirect, url_for

from .smtp_utils import get_recipients, get_message_body, generate_preview, batch_send_emails


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
    body_extension = get_file_extension(body_file.filename)
    recipients_extension = get_file_extension(recipients_file.filename)
    # current_time = time.strftime('%Y%m%d-%H%M%S')
    # body_path = os.path.join(app.config['UPLOAD_DIR'], current_time + body_extension)
    # recipients_path = os.path.join(app.config['UPLOAD_DIR'], current_time + recipients_extension)
    body_filename = str(uuid.uuid1()) + body_extension
    recipients_filename = str(uuid.uuid1()) + recipients_extension
    body_file.save(os.path.join(app.config['UPLOAD_DIR'], body_filename))
    recipients_file.save(os.path.join(app.config['UPLOAD_DIR'], recipients_filename))

    return jsonify({'message': 'Success', 'data': {'bodyName': body_filename, 'recipientsName': recipients_filename}})


@app.route('/preview', methods=['GET'])
def email_preview():
    body_filename = request.args.get('bodyName')
    recipients_filename = request.args.get('recipientsName')
    body = get_message_body(os.path.join(app.config['UPLOAD_DIR'], body_filename))
    recipients = get_recipients(os.path.join(app.config['UPLOAD_DIR'], recipients_filename))

    return generate_preview(body, recipients)


@app.route('/send', methods=['POST'])
def send_emails():
    body_filename = request.json.get('bodyName')
    recipients_filename = request.json.get('recipientsName')
    body = get_message_body(os.path.join(app.config['UPLOAD_DIR'], body_filename))
    recipients = get_recipients(os.path.join(app.config['UPLOAD_DIR'], recipients_filename))

    credentials = (app.config['EMAIL_ADDR'], app.config['EMAIL_PWD'])
    print(body, recipients)
    batch_send_emails(credentials, recipients, body)
    return jsonify({'message': 'Success'})


def get_file_extension(filename):
    if '.' not in filename:
        return ''
    return '.' + filename.rsplit('.', 1)[1].lower()
