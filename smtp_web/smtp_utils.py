import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, formataddr
from pathlib import Path

import openpyxl
import markdown2

from . import socketio


def get_recipients(filepath: str) -> list[dict]:
    file = Path(filepath)
    if file.suffix == '.xlsx': # Note all suffixes should be in lowercase by now
        return _read_excel_data(filepath)
    elif file.suffix == '.csv':
        raise NotImplementedError


def _read_excel_data(filepath):
    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active
    rows = sheet.rows
    recipients = []

    extras_keys = {}
    for i, cell in enumerate(next(rows)):
        if i in (0, 1):
            continue
        if cell.value is None or cell.value.strip() == '':
            continue
        extras_keys[i] = cell.value.lower()

    for row in rows:
        if row[0].value is None:
            continue
        if row[0].value.strip() == '': # TODO: add regex email address check
            continue
    
        recipient = {
            'address': row[0].value,
            'name': row[1].value or '',
            'extras': {key: row[i].value or '' for i, key in extras_keys.items()}
        }
        recipients.append(recipient)

    return recipients


def get_message_body(filepath):
    with open(filepath, encoding='UTF-8') as f:
        raw_markdown = f.read()
    with open('smtp_web/email_template.html', encoding='UTF-8') as f:
        template_html = f.read()
    message_body = md2html(raw_markdown)
    message_body = re.sub(r'{{message_body}}', message_body, template_html)
    message_body = minimize(message_body)
    return message_body


def md2html(message_body):
    message_body = markdown2.markdown(message_body, extras=['break-on-newline'])
    return message_body


def minimize(message_body):
    # TODO: implement
    return message_body


def format_message(message_body, recipient):
    message_body = re.sub(r'{{ *name *}}', recipient['name'], message_body)
    for key, val in recipient['extras'].items():
        message_body = re.sub(r'{{ *' + key + r' *}}', str(val), message_body)
    return message_body


def generate_preview(template_body, recipients):
    message_body = format_message(template_body, recipients[0])
    return message_body


def batch_send_emails(credentials, subject, recipients, template_body, reply_to=None, attachments=None, att_dir=None, room=None, logger=None, is_plain_text=False):
    # Authentication
    if logger is None:
        print('[INFO] Authenticating...')
    else:
        logger.info('Authenticating...')
    if room is not None:
        socketio.emit('message', {'message': '邮箱登录中……'}, to=room)

    mailserver = smtplib.SMTP('smtp.office365.com', 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.login(*credentials)

    # Start batch sending emails
    if logger is None:
        print('[INFO] Start batch sending emails.')
    else:
        logger.info('Start batch sending emails.')
    if room is not None:
        socketio.emit('message', {'message': '开始发送……'}, to=room)
    total_length = len(recipients)
    for i, recipient in enumerate(recipients):
        message = MIMEMultipart()
        message['From'] = formataddr(('Oxford China Forum', credentials[0]))
        if reply_to is not None:
            if isinstance(reply_to, str):
                message['Reply-To'] = reply_to
            else:
                message['Reply-To'] = formataddr(reply_to[:2])
        message['To'] = recipient['address']
        message['Subject'] = subject
        message['Date'] = formatdate(localtime=True)

        # Format the template message body with recipient info
        message_body = format_message(template_body, recipient)
        message.attach(MIMEText(message_body, 'plain' if is_plain_text else 'html', 'utf-8'))

        # Attach email attachments
        for attachment in attachments or []:
            filepath = os.path.join(att_dir or '', attachment['saveName'])
            display_name = attachment['displayName']
            with open(filepath, 'rb') as f:
                part = MIMEApplication(f.read())
                part.add_header('Content-Disposition', 'attachment', filename=Header(display_name, 'utf-8').encode())
                # The following line, despite being used almost everywhere, fails to work
                # for certain clients, resulting in attachments being displayed simply as "2"
                # part.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', display_name))
                message.attach(part)

        try:
            mailserver.sendmail(credentials[0], recipient['address'], message.as_string())
            message = f'({i+1}/{total_length}) 成功发送 {recipient["address"]}'
            if logger is None:
                print(f'[INFO] {message}')
            else:
                logger.info(message)
            if room is not None:
                socketio.emit('message', {'message': message, 'type': 'success'}, to=room)
        except Exception:
            message = f'({i+1}/{total_length}) 发送失败 {recipient["address"]}'
            if logger is None:
                print(f'[WARNING] {message}')
            else:
                logger.warning(message)
            if room is not None:
                socketio.emit('message', {'message': message, 'type': 'danger'}, to=room)

    mailserver.quit()
