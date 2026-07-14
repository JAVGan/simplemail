import os
import tempfile
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from simplemail.cli import (
    check_ports_mapping,
    load_configuration,
    send_email,
    set_defaults,
)


def _make_options(**overrides):
    defaults = dict(
        sender="from@example.com",
        to=["to@example.com"],
        cc=None,
        bcc=None,
        subject=None,
        smtp_server=None,
        smtp_user=None,
        smtp_password=None,
        tls=None,
        ssl=None,
        content_type=None,
        charset=None,
        log_level=None,
        log_file=None,
        smtp_debug=None,
        body=["Hello"],
        file=None,
        config_file=None,
    )
    defaults.update(overrides)
    return Namespace(**defaults)


# ---------------------------------------------------------------------------
# check_ports_mapping
# ---------------------------------------------------------------------------
class TestCheckPortsMapping:
    def test_port_25_tls_false(self):
        assert check_ports_mapping("25", "tls") is False

    def test_port_25_ssl_false(self):
        assert check_ports_mapping("25", "ssl") is False

    def test_port_465_ssl_true(self):
        assert check_ports_mapping("465", "ssl") is True

    def test_port_587_tls_true(self):
        assert check_ports_mapping("587", "tls") is True

    def test_port_2525_tls_true(self):
        assert check_ports_mapping("2525", "tls") is True

    def test_unmapped_port_returns_false(self):
        assert check_ports_mapping("9999", "tls") is False


# ---------------------------------------------------------------------------
# set_defaults
# ---------------------------------------------------------------------------
class TestSetDefaults:
    def test_all_none_gets_defaults(self):
        opts = _make_options()
        opts = set_defaults(opts)
        assert opts.subject == "(no subject)"
        assert opts.smtp_server == "localhost:25"
        assert opts.tls == "auto"
        assert opts.ssl == "auto"
        assert opts.content_type == "text/html"
        assert opts.charset == "utf-8"
        assert opts.log_level == "INFO"
        assert opts.smtp_debug == "false"
        assert opts.smtp_user == ""
        assert opts.smtp_password == ""

    def test_preset_values_preserved(self):
        opts = _make_options(
            subject="Important",
            smtp_server="mail.example.com:587",
            tls="true",
            ssl="false",
            content_type="text/plain",
            charset="ascii",
            log_level="DEBUG",
            smtp_debug="true",
            smtp_user="user",
            smtp_password="pass",
        )
        opts = set_defaults(opts)
        assert opts.subject == "Important"
        assert opts.smtp_server == "mail.example.com:587"
        assert opts.tls == "true"
        assert opts.ssl == "false"
        assert opts.content_type == "text/plain"
        assert opts.charset == "ascii"
        assert opts.log_level == "DEBUG"
        assert opts.smtp_debug == "true"
        assert opts.smtp_user == "user"
        assert opts.smtp_password == "pass"

    def test_partial_values(self):
        opts = _make_options(subject="Test", tls="true")
        opts = set_defaults(opts)
        assert opts.subject == "Test"
        assert opts.tls == "true"
        assert opts.smtp_server == "localhost:25"
        assert opts.ssl == "auto"


# ---------------------------------------------------------------------------
# load_configuration
# ---------------------------------------------------------------------------
class TestLoadConfiguration:
    def _write_ini(self, content):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".ini", delete=False
        )
        f.write(content)
        f.close()
        return f.name

    def test_full_config(self):
        path = self._write_ini(
            "[SMTP]\n"
            'Host = "smtp.test.com"\n'
            'Port = "587"\n'
            'Username = "user"\n'
            'Password = "pass"\n'
            'UseSSL = "false"\n'
            'UseTLS = "true"\n'
            "\n"
            "[MESSAGE]\n"
            'Content = "hello world"\n'
            'Subject = "subj"\n'
            'ContentType = "text/plain"\n'
            'Charset = "ascii"\n'
            "\n"
            "[LOGGING]\n"
            'LogLevel = "DEBUG"\n'
            'LogFile = "/tmp/test.log"\n'
            'SmtpDebug = "true"\n'
        )
        try:
            opts = _make_options(config_file=path, body=None)
            opts = load_configuration(opts)
            assert opts.smtp_server == "smtp.test.com:587"
            assert opts.smtp_user == "user"
            assert opts.smtp_password == "pass"
            assert opts.ssl == "false"
            assert opts.tls == "true"
            assert opts.body == "hello world"
            assert opts.subject == "subj"
            assert opts.content_type == "text/plain"
            assert opts.charset == "ascii"
            assert opts.log_level == "DEBUG"
            assert opts.log_file == "/tmp/test.log"
            assert opts.smtp_debug == "true"
        finally:
            os.unlink(path)

    def test_cli_args_override_config(self):
        path = self._write_ini(
            "[SMTP]\n"
            'Host = "smtp.test.com"\n'
            'Port = "587"\n'
            'Username = "config_user"\n'
        )
        try:
            opts = _make_options(
                config_file=path,
                smtp_server="override.com:25",
                smtp_user="cli_user",
            )
            opts = load_configuration(opts)
            assert opts.smtp_server == "override.com:25"
            assert opts.smtp_user == "cli_user"
        finally:
            os.unlink(path)

    def test_smtp_only_section(self):
        path = self._write_ini(
            "[SMTP]\n"
            'Host = "smtp.test.com"\n'
            'Port = "25"\n'
        )
        try:
            opts = _make_options(config_file=path)
            opts = load_configuration(opts)
            assert opts.smtp_server == "smtp.test.com:25"
        finally:
            os.unlink(path)

    def test_missing_smtp_section_exits(self):
        path = self._write_ini("[MESSAGE]\nContent = test\n")
        try:
            with pytest.raises(SystemExit):
                opts = _make_options(config_file=path)
                load_configuration(opts)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# send_email
# ---------------------------------------------------------------------------
class TestSendEmail:
    def _ready_options(self, **overrides):
        opts = _make_options(**overrides)
        return set_defaults(opts)

    @patch("simplemail.cli.smtplib.SMTP")
    def test_successful_send_returns_0(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        opts = self._ready_options()
        assert send_email(opts) == 0
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch("simplemail.cli.smtplib.SMTP")
    def test_smtp_exception_returns_1(self, mock_smtp_cls):
        mock_smtp_cls.side_effect = Exception("connection refused")
        opts = self._ready_options()
        assert send_email(opts) == 1

    @patch("simplemail.cli.smtplib.SMTP")
    def test_with_cc_and_bcc(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        opts = self._ready_options(
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        assert send_email(opts) == 0
        call_args = mock_server.sendmail.call_args
        recipients = call_args[0][1]
        assert "cc@example.com" in recipients
        assert "bcc@example.com" in recipients

    @patch("simplemail.cli.smtplib.SMTP")
    def test_with_file_attachment(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"attachment content")
            attachment_path = f.name
        try:
            opts = self._ready_options(file=[attachment_path])
            assert send_email(opts) == 0
        finally:
            os.unlink(attachment_path)

    @patch("simplemail.cli.smtplib.SMTP")
    def test_body_from_file(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".html"
        ) as f:
            f.write("<h1>Hello</h1>")
            body_path = f.name
        try:
            opts = self._ready_options(body=[body_path])
            assert send_email(opts) == 0
        finally:
            os.unlink(body_path)

    @patch("simplemail.cli.smtplib.SMTP_SSL")
    def test_ssl_connection(self, mock_smtp_ssl_cls):
        mock_server = MagicMock()
        mock_smtp_ssl_cls.return_value = mock_server
        opts = self._ready_options(
            smtp_server="mail.example.com:465",
            ssl="true",
            tls="false",
        )
        assert send_email(opts) == 0
        mock_smtp_ssl_cls.assert_called_once_with("mail.example.com", "465")

    @patch("simplemail.cli.smtplib.SMTP")
    def test_tls_connection(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        opts = self._ready_options(
            smtp_server="mail.example.com:587",
            tls="true",
            ssl="false",
        )
        assert send_email(opts) == 0
        mock_server.starttls.assert_called_once()


# ---------------------------------------------------------------------------
# main (argument parsing)
# ---------------------------------------------------------------------------
class TestMain:
    def test_missing_required_args_exits(self):
        with patch("sys.argv", ["simplemail"]):
            with pytest.raises(SystemExit):
                from simplemail.cli import main
                main()

    def test_no_body_or_attachment_exits(self):
        with patch(
            "sys.argv",
            ["simplemail", "-f", "a@b.com", "-t", "c@d.com"],
        ):
            with pytest.raises(SystemExit):
                from simplemail.cli import main
                main()
