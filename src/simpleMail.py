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
import configparser
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
        body = str(''.join(options.body))
        if os.path.isfile(body):
            f = open(body, 'r')
            body = ''.join(f.readlines())
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


# -- Function: load_configuration
# It retrieves the configuration from external file and override the default options
# while preserving the values passed as arguments
#
def load_configuration(options):
    config = configparser.ConfigParser()
    try:
        config.read(options.config_file)
     
        # SMTP - Mandatory section
        smtp_section = config["SMTP"]
        options.smtp_server = smtp_section["Host"].strip('"') + ":" + smtp_section["Port"].strip('"') if not options.smtp_server else options.smtp_server
        if "Username" in smtp_section:
            options.smtp_user = smtp_section["Username"].strip('"') if not options.smtp_user else options.smtp_user
        if "Password" in smtp_section:
            options.smtp_password = smtp_section["Password"].strip('"') if not options.smtp_password else options.smtp_password
        if "UseSSL" in smtp_section:
            options.ssl = smtp_section["UseSSL"].strip('"') if not options.ssl else options.ssl
        if "UseTLS" in smtp_section:
            options.tls = smtp_section["UseTLS"].strip('"') if not options.tls else options.tls
        
        # MESSAGE - Optional section 
        if "MESSAGE" in config.sections():
            message_section = config["MESSAGE"]
            options.body = message_section["Content"].strip('"') if not options.body else options.body
            if "Subject" in message_section:
                options.subject = message_section["Subject"].strip('"') if not options.subject else options.subject
            if "ContentType" in message_section:
                options.content_type = message_section["ContentType"].strip('"') if not options.content_type else options.content_type
            if "Charset" in message_section:
                options.charset = message_section["Charset"].strip('"') if not options.charset else options.charset
                
        # LOGGING - Optional section
        if "LOGGING" in config.sections():
            logging_section = config["LOGGING"]
            options.log_level = logging_section["LogLevel"].strip('"') if not options.log_level else options.log_level
            if "LogFile" in logging_section:
                options.log_file = logging_section["LogFile"].strip('"') if not options.log_file else options.log_file
            if "SmtpDebug" in logging_section:
                options.smtp_debug = logging_section["SmtpDebug"].strip('"') if not options.smtp_debug else options.smtp_debug
                
    except Exception as e:
        print("CRITICAL: Failed to load the configuration file \"%s\": %s" % (options.config_file, e))
        sys.exit(1)
    return options


# -- Function set_defaults
# It set defaut options for values not passed as arugments.
#
# Even tough it's possible use the "default" key on argparse we're not doing it here
# because if we set a default before calling the function load_configuration it would
# difficult the decision to preserve the original arguments
def set_defaults(options):
    options.subject = "(no subject)" if not options.subject else options.subject
    options.smtp_server = "localhost:25" if not options.smtp_server else options.smtp_server
    options.tls = "auto" if not options.tls else options.tls
    options.ssl = "auto" if not options.ssl else options.ssl
    options.content_type = "text/html" if not options.content_type else options.content_type
    options.charset = "utf-8" if not options.charset else options.charset
    options.log_level = "INFO" if not options.log_level else options.log_level
    options.smtp_debug = "false" if not options.smtp_debug else options.smtp_debug
    options.smtp_user = "" if not options.smtp_user else options.smtp_user
    options.smtp_password = "" if not options.smtp_password else options.smtp_password
    return options


# ------------------------------------------- Main ------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Send an email using an SMTP server")
    
    # Required arguments
    required = parser.add_argument_group('required arguments')
    required.add_argument("-f", "--sender", dest='sender', metavar="MAIL_ADDRESS", help="The sender email address", required=True)
    required.add_argument("-t", "--to", dest='to', metavar="MAIL_ADDRESS", help="The recipient email address(es)",nargs='+', required=True)
    
    # Optional arguments
    # We should not set the defaults here since it will mess the decision taking of "load_configuration" to preserve the arguments 
    parser.add_argument("-c", "--config-file", dest='config_file', metavar="CONFIG_FILE", help="The configuration file in INI format")
    parser.add_argument("-xu", "--smtp_user", dest='smtp_user', metavar="USERNAME", help="The username for SMTP authentication")
    parser.add_argument("-xp", "--smtp_password", dest='smtp_password', metavar="PASSWORD", help="The password for SMTP authentication")
    parser.add_argument("-cc", "--cc", dest='cc', metavar="MAIL_ADDRESS", help="The cc email address(es)", nargs='*')
    parser.add_argument("-bcc", "--bcc", dest='bcc', metavar="MAIL_ADDRESS", help="The bcc email address(es)", nargs='*')
    parser.add_argument("-u", "--subject", dest='subject', metavar="SUBJECT", help="The message subject. Default = \"(no subject)\"")
    parser.add_argument("-s", "--server", dest='smtp_server', metavar="SERVER[:PORT]", help="The smtp server in the format \"host:port\". Default = localhost:25")
    parser.add_argument("-m", "--message", dest='body', metavar="MESSAGE", help="The message body. It can also be the path of a file with the message body", nargs='*')
    parser.add_argument("-a", "--attachments", dest='file', metavar="FILE", help="File attachment(s)", nargs='*')
    parser.add_argument("--tls", dest='tls', metavar="<true|false|auto>", help="Whether use TLS or not. Default = auto")
    parser.add_argument("--ssl", dest='ssl', metavar="<true|false|auto>", help="Whether use SSL or not. Default = auto")
    parser.add_argument("--content-type", dest='content_type', metavar="TYPE", help="The message body type. Default = \"text/html\"")
    parser.add_argument("--charset", dest='charset', metavar="CHARSET", help="The message body character encoding. Default = \"utf-8\"")
    parser.add_argument("--log-level", dest='log_level', metavar="DEBUG|INFO|WARNING|ERROR|CRITICAL", help='the log level. Defatult = INFO')
    parser.add_argument("--log-file", dest='log_file', metavar="FILE", help='log into a file instead of using STDOUT.')
    parser.add_argument("--smtp-debug", dest="smtp_debug", metavar="<true|false>", help="whether to enable debugging for SMTP communication. Default = false")
    
    # Read the arguments
    options = parser.parse_args()
    
    # Load configuration from file if any
    if options.config_file:
        options = load_configuration(options)
    
    # Set default values after "load_configuration" to preserve the original arguments
    options = set_defaults(options)
    
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
        parser.error("must specify message body or attachement to send in message")

    # Execution
    sys.exit(send_email(options))


