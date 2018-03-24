import ConfigParser
import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from smtplib import SMTP, SMTP_SSL

import requests

import tdtool

# Global variables
project = 'MonFreezeDoor'
INI_file = project + '.conf'
LOG_file = project + '.log'
FreezerID = 1595686  # freezer door switch dummy device
BellID = 395273


def get_vault(uid):
    url = config.get('vault', 'vault_url')
    r = requests.get(url=url + '?uid=%s' % uid)
    id = r.json()
    r.close()
    if id['status'] == 200:
        _username = id['username']
        _password = id['password']
    else:
        _username = ''
        _password = ''
    return _username, _password


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
        maxBytes=500000,
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
    try:
        with open(f, 'r+') as config_file:
            config_ = ConfigParser.SafeConfigParser()
            config_.readfp(config_file)
    except IOError:
        pass
    if config_ is None:
        log_.critical('configuration file is missing')
    return config_


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
    # retrieve the USERNAME & PASSWORD
    # retrieve the PASSWORD
    try:
        uid = config.get('smtp', 'uid')
    except ConfigParser.NoOptionError:
        log.critical('no uid option in configuration')
        return

    try:
        USERNAME, PASSWORD = get_vault(uid)

    except ConfigParser.NoOptionError:
        log.critical('Cannot retrieve user name from vault')
        return

    # retrieve the ssl flag
    try:
        SSL = config.get('smtp', 'ssl')
    except ConfigParser.NoOptionError:
        SSL = False

    try:
        if SSL == 'True':
            conn = SMTP_SSL(HOST, PORT)
            conn.ehlo()
        else:
            conn = SMTP()
            conn.connect(HOST, PORT)
            conn.ehlo()
            conn.starttls()
            conn.ehlo()

        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)

        msg = "\r\n".join([
            "From: %s" % SENDER,
            "To: %s" % address,
            "Subject: %s" % subject,
            "",
            content])
        conn.sendmail(SENDER, address, msg)
        conn.close()

    except Exception, e:
        log.critical('Couldn''t send mail: %s - error %s' % (subject, e))


def main():
    bDeb = False

    while True:
        old_bDeb = bDeb
        config.read(INI_file)
        bDeb = config.get('Freezer', 'DEV')

        if bDeb == 'True':
            timeout = 5  # seconds
            timeout2 = 60
            if old_bDeb != bDeb:
                log.info('Now in Debug mode')
        else:
            timeout = int(config.get('Freezer', 'timeout'))  # seconds
            timeout2 = int(config.get('Freezer', 'timeout2'))
            if old_bDeb != bDeb:
                log.info('Now in Normal mode')

        state = None

        try:
            state = tdtool.getDeviceState(deviceID=FreezerID)
            if state != 'OFF':
                log.info('state: %s' % state)
        except Exception, e:
            print 'Telldus - Error %s' % e

        if state == 'ON':
            sincetime = time.strftime("%d/%m/%Y - %H:%M")
            time.sleep(timeout)
            try:
                state = tdtool.getDeviceState(deviceID=FreezerID)
                if state != 'OFF':
                    log.info('state: %s' % state)

                while state == 'ON':
                    alarm = 'Alarm: Freezer door is opened since %s ' % sincetime
                    log.critical(alarm)
                    # if bDeb != 'True':
                    #     tdtool.doMethod(BellID, tdtool.TELLSTICK_TURNON)
                    #     tdtool.doMethod(BellID, tdtool.TELLSTICK_TURNOFF)
                    #     send_mail('joelle@mayeur.be', 'Alarme Surgelateur - Porte ouverte', alarm)
                    send_mail('xavier@mayeur.be', 'Alarme Surgelateur - Porte ouverte', alarm)

                    time.sleep(timeout2)
                    try:
                        state = tdtool.getDeviceState(deviceID=FreezerID)
                    except Exception, e:
                        log.warning('Telldus - Error %s' % e)

                    if state != 'OFF':
                        log.info('state: %s' % state)

                if state == 'OFF':
                    log.warning('Freezer door was finally closed at %s' % time.strftime("%d/%m/%Y - %H:%M"))

            except Exception, e:
                log.warning('Telldus - Error %s' % e)

        else:
            time.sleep(timeout)


if __name__ == "__main__":
    main()
