import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
        if cell.value.strip() == '':
            continue
        extras_keys[i] = cell.value.lower()

    for row in rows:
        if row[0].value.strip() == '': # TODO: add regex address check
            continue
    
        recipient = {
            'address': row[0].value,
            'name': row[1].value,
            'extras': {key: row[i].value for i, key in extras_keys.items()}
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


def batch_send_emails(credentials, subject, recipients, template_body, room=None, logger=None, is_plain_text=False):
    # 登录邮箱服务器
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

    # 批量发送邮件
    if logger is None:
        print('[INFO] Start batch sending emails.')
    else:
        logger.info('Start batch sending emails.')
    if room is not None:
        socketio.emit('message', {'message': '开始发送……'}, to=room)
    total_length = len(recipients)
    for i, recipient in enumerate(recipients):
        message = MIMEMultipart()
        message['From'] = f'Oxford China Forum <{credentials[0]}>'
        message['To'] = recipient['address']
        message['Subject'] = subject

        # 用收件人信息替换模板占位符
        message_body = format_message(template_body, recipient)
        message.attach(MIMEText(message_body, 'plain' if is_plain_text else 'html', 'utf-8'))

        # TODO: handle attachments
        # att1 = MIMEText(open('123.pdf', 'rb').read(), 'base64', 'utf-8')
        # att1['Content-Type'] = 'application/octet-stream'
        # att1['Content-Disposition'] = 'attachment; filename='123.pdf''
        # message.attach(att1)
        ...

        try:
            mailserver.sendmail(credentials[0], recipient['address'], message.as_string())
            if logger is None:
                print(f'[INFO] ({i+1}/{total_length}) 成功发送 {recipient["address"]}')
            else:
                logger.info(f'({i+1}/{total_length}) 成功发送 {recipient["address"]}')
            if room is not None:
                socketio.emit('message', {'message': f'({i+1}/{total_length}) 成功发送 {recipient["address"]}', 'type': 'success'}, to=room)
        except smtplib.SMTPException:
            if logger is None:
                print(f'[WARNING] ({i+1}/{total_length}) 发送失败 {recipient["address"]}')
            else:
                logger.warning(f'({i+1}/{total_length}) 发送失败 {recipient["address"]}')
            if room is not None:
                socketio.emit('message', {'message': f'({i+1}/{total_length}) 发送失败 {recipient["address"]}', 'type': 'danger'}, to=room)

    mailserver.quit()


if __name__ == '__main__':
    print('欢迎使用 OCF 群发邮件脚本。\n')
    while True:
        recipients_path = input('请输入收件人列表文件路径（可以直接拖拽文件），留空则使用 "recipients.xlsx"：') or 'recipients.xlsx'
        if Path(recipients_path).is_file():
            break
        print('[ERROR] 文件路径不存在或错误，请重试')
    while True:
        body_path = input('请输入邮件内容文件路径（可以直接拖拽文件），留空则使用 "body.md"：') or 'body.md'
        if Path(body_path).is_file():
            break
        print('[ERROR] 文件路径不存在或错误，请重试')
    print()

    recipients = get_recipients(recipients_path)
    message_body = get_message_body(body_path)

    batch_send_emails(recipients, message_body)
