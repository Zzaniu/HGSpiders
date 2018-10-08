import sys
import functools
import traceback
import smtplib
import email.mime.multipart
import email.mime.text
from email.utils import formataddr

from conf.settings import EMAIL_PWD, SEND_EMAIL
from lib.log import getSpiderLogger
log = getSpiderLogger()


def send_email(text, subject):
    """
    发送邮件
    :param text: 需要发送的字符串
    :param subject: 发邮件的主题
    :return: 
    """
    # to_email = 'Michael.song@betterbt.com,zaniu.zeng@betterbt.com'
    to_email = 'zaniu.zeng@betterbt.com'
    smtp_server = 'smtp.126.com'

    msg = email.mime.multipart.MIMEMultipart()
    msg['from'] = formataddr(['ZzaniuzzZ', SEND_EMAIL])
    msg['to'] = to_email
    msg['subject'] = subject

    content = text
    txt = email.mime.text.MIMEText(content, _charset='utf-8')
    msg.attach(txt)

    try:
        smtp = smtplib.SMTP(smtp_server, 25)
        smtp.set_debuglevel(1)
        smtp.login(SEND_EMAIL, EMAIL_PWD)
        smtp.sendmail(SEND_EMAIL, to_email.split(','), msg.as_string())
        smtp.quit()
    except Exception as e:
        log.exception(e)
        log.error("邮件发送异常,极有可能是邮件发送功能被禁止.")


def error_2_send_email(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            send_email(text=str(traceback.format_exc()), subject="爬虫程序运行出错，请前往查看")
            log.error("爬虫程序运行出错，请前往查看，错误信息{}".format(str(traceback.format_exc())))
            sys.exit(-1)

    return wrapper


if __name__ == "__main__":
    send_email('女朋友约你', subject="女朋友找你")
