import commands
import platform
import smtplib
from email.mime.text import MIMEText
from time import sleep
import argparse


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
    parser = argparse.ArgumentParser(description='email notification')
    parser.add_argument('--email', '-e', help='email address', required=True)
    parser.add_argument('--process', '-p', help='process', required=True)
    parser.add_argument('--title', '-t', help='email content', default='Your process is done')
    parser.add_argument('--content', '-c', help='email content')
    args = parser.parse_args()

    host = platform.node()
    process = args.process
    email = args.email
    title = args.title
    content = args.content if args.content else '{} is done'.format(process)

    print commands.getoutput('ps -ef | grep %s' % process).split('\n')
    while any([True if x.find('python %s' % process) >= 0 else False
               for x in commands.getoutput('ps -ef | grep %s' % process).split('\n')]):
        print 'sleep ...'
        sleep(300)
    send_email(title, host, email, content)


if __name__ == '__main__':
    main()
