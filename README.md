# simplemail
A simple e-mail sender in Python


## Getting Started

This project provides a simple and portable python script which can be used to send e-mails by SMTP.

It will use the parameters received as arguments to process the mail request.


### Prerequisites

Python 3 installation with smtplib


### Installing

Just copy the file simpleMail.py to your preferred working directory and call it with their Python 3 interpreter

```
cp src/simpleMail.py YOUR_DIRECTORY
```



### Execution

In order to execute the simplemail use:
```
python simpleMail.py [ARGS]
```

Where the minimal arguments are:
```
-f [MAIL_ADDRESS]     # The sender email address
                    
-t [MAIL_ADDRESSESS]  # The recipient email address(es)

```

It's possible to store the default values for SMTP, MESSAGE and LOGGING in a config.ini file to avoid passing them in command line everytime.
Check the internal docs on [configuration_example.ini](templates/configuration_example.ini) to know how to configure it
```
python simpleMail.py -f "from@example.com" -t "to@exmple.com" -c "templates/configuration_example.ini"
```


Optional arguments:
```
-c [CONFIG_FILE]      # The configuration file in INI format

-m [MESSAGE ...]      # The message content (body). It can be a file with the content or a string with the raw text

-xu [USERNAME]        # The username for SMTP authentication

-xp [PASSWORD]        # The password for SMTP authentication

-cc [MAIL_ADDRESS ...]   # The cc email address(es)

-bcc [MAIL_ADDRESS ...]  # The bcc email address(es)

-u [SUBJECT]             # The message subject. Default = "(no subject)"

-s SERVER[:PORT],        # The smtp server in the format "host:port". Default = localhost:25

-a [FILE ...]            # File attachment(s)

--tls <true|false|auto>  # Whether use TLS or not. Default = auto

--ssl <true|false|auto>  # Whether use SSL or not. Default = auto

--content-type [TYPE]    # The message body type. Default = "text/html"

--charset [CHARSET]      # The message body character encoding. Default = "utf-8"

--log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]   # The log level. Defatult = INFO

--log-file [FILE]        # log into a file instead of using STDOUT.

--smtp-debug <true|false> # whether to enable debugging for SMTP communication. Default = false
```

The complete list of arguments can be found by executing:

```
python simpleMail.py --help
```



## Authors

* **Jonathan Gangi** - *Initial work* - [JAVGan](https://github.com/JAVGan/)


## License

This project is licensed under the GNU LESSER GENERAL PUBLIC LICENSE v2.1 - see the [LICENSE](LICENSE) file for details



