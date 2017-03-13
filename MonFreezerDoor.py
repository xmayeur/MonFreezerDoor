import tdtool
import sys
import time
from smtplib import SMTP, SMTP_SSL
import ConfigParser
import Key
import logging
from logging.handlers import RotatingFileHandler
from crypto_helpers import AEScipher
import os

project = 'MonFreezeDoor'
INI_file = project + '.conf'
LOG_file = project + '.log'
FreezerID = 1595686  # freezer door switch dummy device
BellID = 395273

timeout = 5  # seconds
timeout2 = 300
tdtool.init(INI_file)
# Initialize cipher object to decrypt password
aes = AEScipher(Key.key)

def open_log(name):
    # Setup the log handlers to stdout and file.
    log_ = logging.getLogger(name)
    log_.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setLevel(logging.DEBUG)
    handler_stdout.setFormatter(formatter)
    log_.addHandler(handler_stdout)
    handler_file = RotatingFileHandler(
        LOG_file,
        mode='a',
        maxBytes=200000,
        backupCount=9,
        encoding='UTF-8',
        delay=True
    )
    handler_file.setLevel(logging.DEBUG)
    handler_file.setFormatter(formatter)
    log_.addHandler(handler_file)
    return log_
log = open_log(project)


def open_config(f):
    log_ = open_log(project + '.open_config')
    # Read config file - halt script on failure
    config_ = None
    for loc in os.curdir, os.path.expanduser('~').join('.' + project), os.path.expanduser('~'), \
               '/etc/' + project, os.environ.get(project + '_CONF'):
        try:
            with open(os.path.join(loc, f), 'r+') as config_file:
                config_ = ConfigParser.SafeConfigParser()
                config_.readfp(config_file)
                break
        except IOError:
            pass
    if config_ is None:
        log_.critical('configuration file is missing')
    return config_
# Open config file
config = open_config(INI_file)


def send_mail(address, subject, content):
    """

    :param address:
    :param subject:
    :param content:
    :return:

    See http://stackoverflow.com/questions/3362600/how-to-send-email-attachments-with-python
    """
    # retrieve the HOST name

    try:
        HOST = config.get('smtp', 'host')
    except ConfigParser.NoOptionError:
        log.critical('no "host" option in configuration')
        return
    # retrieve the port
    try:
        PORT = config.get('smtp', 'port')
    except ConfigParser.NoOptionError:
        log.critical('no "port" option in configuration')
        return
    # retrieve the sender
    try:
        SENDER = config.get('smtp', 'sender')
    except ConfigParser.NoOptionError:
        log.critical('no "sender" option in configuration')
        return
    # retrieve the USERNAME
    try:
        USERNAME = config.get('smtp', 'username')
    except ConfigParser.NoOptionError:
        log.critical('no "username" option in configuration')
        return

    # retrieve the PASSWORD
    try:
        PASSWORD = config.get('smtp', 'password')
    except ConfigParser.NoOptionError:
        log.critical('no "password" option in configuration')
        return

    # retrieve the ssl flag
    try:
        SSL = config.get('smtp', 'ssl')
    except ConfigParser.NoOptionError:
        SSL = False

    try:
        if SSL:
            conn = SMTP_SSL(HOST, PORT)
            conn.ehlo()
        else:
            conn = SMTP()
            conn.connect(HOST, PORT)
            conn.ehlo()
            conn.starttls()
            conn.ehlo()

        conn.set_debuglevel(False)
        conn.login(USERNAME, aes.decrypt(PASSWORD))

        msg = "\r\n".join([
            "From: %s" % SENDER,
            "To: %s" % address,
            "Subject: %s" % subject,
            "",
            content])
        conn.sendmail(SENDER, address, msg)
        conn.close()

    except Exception:
        log.critical('Couldn''t send mail: %s' % subject)


def main():
    while True:
        try:
            state = tdtool.getDeviceState(deviceID=FreezerID)
        except Exception, e:
            print 'Error %s' % e
            sys.exit(1)
        if state == 'ON':
            sincetime = time.strftime("%d/%m/%Y - %H:%M")
            time.sleep(timeout)
            while tdtool.getDeviceState(deviceID=FreezerID) == 'ON':
                alarm = 'Alarm: Freezer door is opened since %s ' % sincetime
                send_mail('xavier@mayeur.be', 'Alarme Surgelateur - Porte ouverte', alarm)
                send_mail('joelle@mayeur.be', 'Alarme Surgelateur - Porte ouverte', alarm)
                log.critical(alarm)
                tdtool.doMethod(BellID, tdtool.TELLSTICK_TURNON)
                tdtool.doMethod(BellID, tdtool.TELLSTICK_TURNOFF)
                time.sleep(timeout2)
            log.warning('Freezer door was finally closed at %s' % time.strftime("%d/%m/%Y - %H:%M"))
        else:
            time.sleep(timeout)


if __name__ == "__main__":
    main()
