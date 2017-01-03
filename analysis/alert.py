import commands
import smtplib
from email.mime.text import MIMEText
from time import sleep


def send_email(subject, sender, receiver, content):
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['to'] = receiver
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, [receiver], msg.as_string())
    s.quit()
    print "send through localhost"


def main():
    while len(commands.getoutput('ps -ef | grep lda').split('\n')) == 3:
        print 'sleep ...'
        sleep(300)
    send_email('done', 'zenixwp', 'smoh2044@gmail.com', 'process done')


if __name__ == '__main__':
    main()
