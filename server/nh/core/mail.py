
from email import header, message
import subprocess
import os

from nh.core.config import CONFIG

def create(to, subject, body):
    """
    Create a python email.message.Message object given the template.

    The body must be Unicode and will be converted using the utf-8 charset.
    """
    msg = message.Message()
    msg["From"] = header.Header(str(CONFIG.EMAIL_FROM))
    msg['To'] = header.Header(str(to))
    if isinstance(subject, unicode):
        msg['Subject'] = header.Header(subject.encode("utf-8"), "utf-8")
    else:
        msg['Subject'] = header.Header(subject)
    msg.set_payload(body.encode("utf-8"), charset="utf-8")
    
    return msg

def send(message):
    """
    Send an email message using sendmail
    """
    if os.environ.has_key("NH_UNITTEST_RUN"):
        message_string = message.as_string(unixfrom=True)
        to = str(message['To']).replace(" ", "_")
        subject = str(message['Subject']).replace(" ", "_")
        output = file("%s/env/test_output/to-%s-for-%s.mbox" % (
                CONFIG.BASE_DIR, to, subject), 'w')
        output.write(message_string)
        output.close()
    else:
        message_string = message.as_string()
        output = subprocess.Popen(
            ["/usr/sbin/sendmail", '-t'], 0, stdin=subprocess.PIPE)
        output.stdin.write(message_string)
                                  
        
        
    
