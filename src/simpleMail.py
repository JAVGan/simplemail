#!/usr/bin/env python
# ----------------------------------------- simpleMail.py -------------------------------------------
# A simple e-mail sender in python.
#
# This software receives the e-mail content from command line and uses a SMTP server to deliver the
# message
# 
# Written by:                                                                                     
#     Jonathan Gangi - javgan.tar.gz@gmail.om
#                                      
# ---------------------------------------------------------------------------------------------------                                                           
#  simpleMail.py
#  Copyright (C) 2021  Jonathan Gangi
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# -------------------------------------------------------------------------------------------------

# ------------------------------------------ Imports ----------------------------------------------
import argparse
import os, sys
import smtplib
import logging

from os.path import basename
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

DEFAULT_PORTS = [ 
        {"port": "25", "tls": False, "ssl": False},
        {"port": "465", "tls": False, "ssl": True},
        {"port": "587", "tls": True, "ssl": False},
        {"port": "2525", "tls": True, "ssl": False}
]

# ----------------------------------------- Functions ---------------------------------------------
# -- Function: sendEmail
# A function to send an e-mail using the arguments received as parameters
#
def send_email(options):    
    try:
        msg = MIMEMultipart()
        msg['From'] = options.sender        
        msg['To'] = COMMASPACE.join(options.to)        
        msg['cc'] = COMMASPACE.join(options.cc) if options.cc else ""
        msg['bcc'] = COMMASPACE.join(options.bcc) if options.bcc else ""
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = options.subject
        options.cc = [] if not options.cc else options.cc
        options.bcc = [] if not options.bcc else options.bcc
        
        logging.debug("Initializing the e-mail sending with the following parameters:")
        logging.debug("    - msg['From'] = %s" % msg['From'])
        logging.debug("    - msg['To'] = %s" % msg['To'])
        logging.debug("    - msg['cc'] = %s" % msg['cc'])
        logging.debug("    - msg['bcc'] = %s" % msg['bcc'])
        logging.debug("    - msg['Date'] = %s" % msg['Date'])
        logging.debug("    - msg['Subject'] = %s" % msg['Subject'])

        # Message body
        logging.debug("Processing the e-mail body:")
        logging.debug("    - content_type: %s" % options.content_type)
        logging.debug("    - charset: %s" % options.charset)
        
        # Check if the message is a file
        body = str(' '.join(options.body))
        if os.path.isfile(body):
            f = open(body, 'r')
            body = '\n'.join(f.readlines())
            f.close()
            
        msg.attach(MIMEText(body,options.content_type.replace('text/',''), _charset=options.charset))
        
        # Process attachements 
        for f in options.file or []:
            logging.debug("Attaching the file \"%s\"" % f)
            with open(f, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=basename(f)
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)

        logging.debug("Connecting to SMTP server:")
        
        # Parse host and port
        smtp_address = options.smtp_server.split(':')
        smtp_host = smtp_address[0]
        smtp_port = smtp_address[1] if len(smtp_address) > 1 else '25'
        
        # Decides the use of SSL/TLS 
        use_tls = True if options.tls.lower().find("true") != -1 else False
        use_tls = check_ports_mapping(smtp_port,"tls") if options.tls.lower().find("auto") != -1 else use_tls
        use_ssl = True if options.ssl.lower().find("true") != -1 else False
        use_ssl = check_ports_mapping(smtp_port,"ssl") if options.ssl.lower().find("auto") != -1 else use_ssl

        logging.debug("    - HOST: %s | PORT: %s | TLS: %s" % (smtp_host, smtp_port, str(use_tls)))
        
        # Initializes the SMTP connection
        server = smtplib.SMTP_SSL(smtp_host, smtp_port) if use_ssl else smtplib.SMTP(smtp_host, smtp_port)
        
        # Set the DEBUG level for SMTP if required
        if options.smtp_debug.lower().find("true") != -1:
            server.set_debuglevel(True)
            
        if use_tls:
            logging.debug("    - starting TLS communication")
            server.starttls()
            
        logging.debug("    - starting login with USERNAME: %s | PASSWORD: %s" % (options.smtp_user, options.smtp_password))
        server.login(options.smtp_user, options.smtp_password)
                
        # Send the message
        logging.debug("Sending e-mail")
        server.sendmail(msg['From'], options.to + options.cc + options.bcc, msg.as_string())
        logging.info("Email sent to: \"%s\"" % msg['To'])
        
        # Close connectino
        logging.debug("Closing the connection with server")
        server.quit()
    except Exception as e:
        logging.error("Failed to process the e-mail request:  \"%s\"" % str(e))
        return 1
    return 0


# -- Function: check_ports_mapping
# A function to check whether use SSL/TLS depending on port
#
def check_ports_mapping(port, method):
    global DEFAULT_PORTS
    res = False
    try:
       res = next(p for p in DEFAULT_PORTS if p["port"] == port)[method]
    except:
        DEBUG("Couldn't determine the SSL/TLS behavior for port \"%s\" - Not mapped" % smtp_port)
    return res


# ------------------------------------------- Main ------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Send an email using an SMTP server")
    
    # Required arguments
    required = parser.add_argument_group('required arguments')
    required.add_argument("-f", "--sender", dest='sender', metavar="MAIL_ADDRESS", help="The sender email address", required=True)
    required.add_argument("-t", "--to", dest='to', metavar="MAIL_ADDRESS", help="The recipient email address(es)",nargs='+', required=True)
    required.add_argument("-m", "--message", dest='body', metavar="MESSAGE", help="The message body. It can also be the path of a file with the message body", nargs='*', required=True)
    required.add_argument("-xu", "--smtp_user", dest='smtp_user', metavar="USERNAME", help="The username for SMTP authentication", required=True)
    required.add_argument("-xp", "--smtp_password", dest='smtp_password', metavar="PASSWORD", help="The password for SMTP authentication", required=True)
    
    # Optional arguments
    parser.add_argument("-cc", "--cc", dest='cc', metavar="MAIL_ADDRESS", help="The cc email address(es)", nargs='*', required=False)
    parser.add_argument("-bcc", "--bcc", dest='bcc', metavar="MAIL_ADDRESS", help="The bcc email address(es)", nargs='*', required=False)
    parser.add_argument("-u", "--subject", dest='subject', metavar="SUBJECT", help="The message subject. Default = \"(no subject)\"", default="(no subject)", required=False)
    parser.add_argument("-s", "--server", dest='smtp_server', default='localhost:25', metavar="SERVER[:PORT]", help="The smtp server in the format \"host:port\". Default = localhost:25", required=False)
    parser.add_argument("-a", "--attachments", dest='file', metavar="FILE", help="File attachment(s)", nargs='*', required=False)
    parser.add_argument("--tls", dest='tls', metavar="<true|false|auto>", default="auto", help="Whether use TLS or not. Default = auto", required=False)
    parser.add_argument("--ssl", dest='ssl', metavar="<true|false|auto>", default="auto", help="Whether use SSL or not. Default = auto", required=False)
    parser.add_argument("--content-type", dest='content_type', metavar="TYPE", default='html', help="The message body type. Default = \"text/html\"", required=False)
    parser.add_argument("--charset", dest='charset', metavar="CHARSET", default='utf-8', help="The message body character encoding. Default = \"utf-8\"", required=False)
    parser.add_argument("--log-level", dest='log_level', metavar="DEBUG|INFO|WARNING|ERROR|CRITICAL", default='INFO', help='the log level. Defatult = INFO', required=False)
    parser.add_argument("--log-file", dest='log_file', default=None, metavar="FILE", help='log into a file instead of using STDOUT.', required=False)
    parser.add_argument("--smtp-debug", dest="smtp_debug", default="false", metavar="<true|false>", help="whether to enable debugging for SMTP communication. Default = false")
    
    # Read the arguments
    options = parser.parse_args()

    # Log initialization
    if options.log_level.lower().find("debug") != -1:
        log_level = logging.DEBUG
    elif options.log_level.lower().find("info") != -1:
        log_level = logging.INFO
    elif options.log_level.lower().find("warning") != -1:
        log_level = logging.WARNING
    elif options.log_level.lower().find("error") != -1:
        log_level = logging.ERROR
    else:
        log_level = logging.CRITICAL

    if options.log_file:
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', filename=options.log_file, filemode='a', level=log_level)
    else:
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=log_level)

    # Message body check
    if (options.body is None or len(options.body) < 1) and options.file is None:
        parser.error("must specify message body as argument or file")

    # Execution
    sys.exit(send_email(options))


