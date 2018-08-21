import sys
import functools
import traceback
import smtplib
import email.mime.multipart
import email.mime.text
from lib.log import getSpiderLogger
log = getSpiderLogger()


def send_email(text,subject):
    """
    发送邮件
    :param text: 需要发送的字符串
    :param subject: 发邮件的主题
    :return: 
    """
    from_email = '2673460873@qq.com'
    password = 'jbdyaaiolwqgdjjf'  # 请注意这里并不是qq邮箱的登录密码,是授权码,授权码是用于登录第三方邮件客户端的专用密码。
    # to_email = 'Michael.song@betterbt.com,zaniu.zeng@betterbt.com'
    to_email = 'zaniu.zeng@betterbt.com'
    smtp_server = 'smtp.qq.com'

    msg = email.mime.multipart.MIMEMultipart()
    msg['from'] = from_email
    msg['to'] = to_email
    msg['subject'] = subject

    content = text
    txt = email.mime.text.MIMEText(content, _charset='utf-8')
    msg.attach(txt)

    try:
        smtp = smtplib.SMTP_SSL(smtp_server,465)
        smtp.set_debuglevel(1)
        smtp.login(from_email, password)
        smtp.sendmail(from_email, to_email.split(','), msg.as_string())
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
