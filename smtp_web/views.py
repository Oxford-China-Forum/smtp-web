import os
import uuid
import time

from flask import current_app as app
from flask import request, session, render_template, jsonify, redirect, url_for
from flask_socketio import join_room, leave_room

from . import socketio
from .smtp_utils import get_recipients, get_message_body, generate_preview, batch_send_emails


@app.route('/', methods=['GET'])
def index_page():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def upload_files():
    if 'body' not in request.files or 'recipients' not in request.files or not request.form.get('subject'):
        return json_resp(code=-1, message='缺失文件或邮件主题为空')
    # Reformat filenames and save files
    body_file = request.files.get('body')
    recipients_file = request.files.get('recipients')
    if body_file is None or body_file.filename == '' or recipients_file is None or recipients_file.filename == '':
        return json_resp(code=-1, message='缺失文件')
    body_extension = get_file_extension(body_file.filename)
    recipients_extension = get_file_extension(recipients_file.filename)
    body_filename = str(uuid.uuid1()) + body_extension
    recipients_filename = str(uuid.uuid1()) + recipients_extension
    body_file.save(os.path.join(app.config['UPLOAD_DIR'], body_filename))
    recipients_file.save(os.path.join(app.config['UPLOAD_DIR'], recipients_filename))

    # Process and save attachments
    attachments = []
    for attachment in request.files.getlist('attachments') or []:
        if attachment is None or attachment.filename == '':
            continue
        extension = get_file_extension(attachment.filename)
        filename = str(uuid.uuid1()) + extension
        attachment.save(os.path.join(app.config['UPLOAD_DIR'], filename))
        attachments.append({'displayName': attachment.filename, 'saveName': filename})

    # File validation
    try:
        get_message_body(os.path.join(app.config['UPLOAD_DIR'], body_filename))
        get_recipients(os.path.join(app.config['UPLOAD_DIR'], recipients_filename))
    except Exception as e:
        # TODO: log these errors
        return json_resp(code=-2, message='文件格式有误，无法读取')

    return json_resp({'bodyName': body_filename, 'recipientsName': recipients_filename, 'attachments': attachments})


@app.route('/preview', methods=['GET'])
def email_preview():
    body_filename = request.args.get('bodyName')
    recipients_filename = request.args.get('recipientsName')
    # TODO: Catch error when generating
    body = get_message_body(os.path.join(app.config['UPLOAD_DIR'], body_filename))
    recipients = get_recipients(os.path.join(app.config['UPLOAD_DIR'], recipients_filename))

    return generate_preview(body, recipients)


@socketio.on('send')
def initialize_send(data):
    room = request.sid
    join_room(room)

    subject = data.get('subject')
    body_filename = data.get('bodyName')
    recipients_filename = data.get('recipientsName')
    attachments = data.get('attachments')

    error_flag = False
    if subject is None or subject == '':
        error_flag = True
    elif body_filename is None or body_filename == '' or not os.path.isfile(os.path.join(app.config['UPLOAD_DIR'], body_filename)):
        error_flag = True
    elif recipients_filename is None or recipients_filename == '' or not os.path.isfile(os.path.join(app.config['UPLOAD_DIR'], recipients_filename)):
        error_flag = True

    if error_flag:
        socketio.emit('message', {'message': '参数有误：缺失文件名或邮件主题为空', 'type': 'danger'}, to=room)
    else:
        body = get_message_body(os.path.join(app.config['UPLOAD_DIR'], body_filename))
        recipients = get_recipients(os.path.join(app.config['UPLOAD_DIR'], recipients_filename))

        credentials = (app.config['EMAIL_ADDR'], app.config['EMAIL_PWD'])
        batch_send_emails(
            credentials,
            subject,
            recipients,
            body,
            reply_to=app.config['REPLY_TO_EMAIL']
            attachments=attachments,
            att_dir=app.config['UPLOAD_DIR'],
            room=room,
            logger=app.logger
        )
        socketio.emit('message', {'message': '发送完成'}, to=room)

    socketio.emit('end', to=room)
    leave_room(room)


def get_file_extension(filename):
    if '.' not in filename:
        return ''
    return '.' + filename.rsplit('.', 1)[1].lower()


def json_resp(data=None, code=0, message='Success'):
    resp_data = {'code': code, 'message': message}
    if data is not None:
        resp_data['data'] = data
    if code != 0 and message == 'Success':
        resp_data['message'] = 'Error'
    return jsonify(resp_data)
