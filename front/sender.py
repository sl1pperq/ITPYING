import smtplib
from email.mime.text import MIMEText

def send_email_message(receiver_mail, text, title):
    port = 465
    password = 'wGsMXpYEHrCcat11M6iT'
    sender_mail = 'ponyatojkina.ks@mail.ru'
    smtp_server = 'smtp.mail.ru'
    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_mail, password)
            msg = MIMEText(f'{text}', 'html')
            msg['Subject'] = title
            msg['From'] = sender_mail
            msg['To'] = receiver_mail
            server.sendmail(sender_mail, receiver_mail, msg.as_string())
    except Exception as e:
        print(e)