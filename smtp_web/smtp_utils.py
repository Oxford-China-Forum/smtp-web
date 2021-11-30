import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import openpyxl
import markdown2


# try:
#     from secrets import EMAIL_ADDR, EMAIL_PWD
# except ImportError:
#     print('[ERROR] No email credentials specified, please consult documentation.')
#     print('Aborting.')
#     exit(-1)


class Recipient:

    def __init__(self):
        self.address = ''
        self.name = ''
        self.extras = {}
    
    def __repr__(self):
        repr_text = f'<{self.address}>'
        if self.name:
            repr_text = f'{self.name} {repr_text}'
        return repr_text
    
    def __str__(self):
        return self.__repr__()
    
    def format_message(self, message_body):
        # TODO: use a better method
        message_body = message_body.replace('{{name}}', self.name)
        message_body = message_body.replace('{{ name }}', self.name)
        for key, val in self.extras:
            message_body = message_body.replace('{{' + key + '}}', val)
            message_body = message_body.replace('{{ ' + key + ' }}', val)
        return message_body


def get_recipients(filepath: str) -> list[Recipient]:
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
    
        recipient = Recipient()
        recipient.address = row[0].value
        recipient.name = row[1].value

        for i, key in extras_keys:
            recipient.extras[key] = row[i].value
        
        recipients.append(recipient)

    return recipients


def get_message_body(filepath):
    with open(filepath, encoding='UTF-8') as f:
        raw_markdown = f.read()
    with open('smtp_web/email_template.html', encoding='UTF-8') as f:
        template_html = f.read()
    message_body = md2html(raw_markdown)
    message_body = template_html.replace('{{message_body}}', message_body)
    message_body = minimize(message_body)
    return message_body


def md2html(message_body):
    message_body = markdown2.markdown(message_body, extras=['break-on-newline'])
    return message_body


def minimize(message_body):
    return message_body


def generate_preview(template_body, recipients):
    message_body = recipients[0].format_message(template_body)


def send_emails(recipients, template_body, is_plain_text=False):
    # 登录邮箱服务器
    print('[INFO] Authenticating...')
    mailserver = smtplib.SMTP('smtp.office365.com', 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.login(EMAIL_ADDR, EMAIL_PWD)

    # 批量发送邮件
    print('[INFO] Start batch sending emails.')
    total_length = len(recipients)
    for i, recipient in enumerate(recipients):
        message = MIMEMultipart()
        message['From'] = f'Oxford China Forum <{EMAIL_ADDR}>'
        message['To'] = recipient.address
        message['Subject'] = 'Welcome to OCF!'

        # 用收件人信息替换模板占位符
        message_body = recipient.format_message(template_body)
        message.attach(MIMEText(message_body, 'plain' if is_plain_text else 'html', 'utf-8'))

        # TODO: handle attachments
        # 在这里设置附件
        # att1 = MIMEText(open('123.pdf', 'rb').read(), 'base64', 'utf-8')
        # att1['Content-Type'] = 'application/octet-stream'
        # att1['Content-Disposition'] = 'attachment; filename='123.pdf''
        # message.attach(att1)
        # 在这里结束设置附件

        try:
            mailserver.sendmail(EMAIL_ADDR, recipient.address, message.as_string())
            print(f'[INFO] ({i+1}/{total_length}) 成功发送 {recipient}')
        except smtplib.SMTPException:
            print(f'[WARNING] ({i+1}/{total_length}) 发送失败 {recipient}')

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

    send_emails(recipients, message_body)
