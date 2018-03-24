#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json
import urllib

import oauth

from MonFreezerDoor import get_vault

PUBLIC_KEY, PRIVATE_KEY = get_vault('telldus_key')
TOKEN, TOKEN_SECRET = get_vault('telldus_apptoken')

TELLSTICK_TURNON = 1
TELLSTICK_TURNOFF = 2
TELLSTICK_BELL = 4
TELLSTICK_DIM = 16
TELLSTICK_UP = 128
TELLSTICK_DOWN = 256

RASPI_ID = 274164
SALON_ID = 223659
SAM_ID = 223659
NAS_ID = 274165

SUPPORTED_METHODS = TELLSTICK_TURNON | TELLSTICK_TURNOFF | TELLSTICK_BELL | TELLSTICK_DIM | TELLSTICK_UP | TELLSTICK_DOWN


def listDevices():
    # type: () -> object
    """

    :rtype :
    """
    response = doRequest('devices/list', {'supportedMethods': SUPPORTED_METHODS})
    # print("Number of devices: %i" % len(response['device']))
    for device in response['device']:
        if device['state'] == TELLSTICK_TURNON:
            state = 'ON'
        elif device['state'] == TELLSTICK_TURNOFF:
            state = 'OFF'
        elif device['state'] == TELLSTICK_DIM:
            state = "DIMMED"
        elif device['state'] == TELLSTICK_UP:
            state = "UP"
        elif device['state'] == TELLSTICK_DOWN:
            state = "DOWN"
        else:
            state = 'Unknown state'
        
        # print ("%s\t%s\t%s" % (device['id'], device['name'], state))
    return json.dumps(response['device'], indent=4, separators=(',', ': '))


# def doJob(id, deviceId, methodId, methodValue=0, type='time', hour, minute, weekdays)
#    response = doRequest('scheduler/setJob', {'id':  id, 'deviceId': deviceId, 'method': methodId,
#  'methodValue': methodValue, 'type': type, 'hour': hour, 'minute': minute, 'weekdays': weekdays})

def getDeviceState(deviceID):
    response = doRequest('device/info', {'id': deviceID, 'supportedMethods': 255})
    val = int(response['state'])
    val2 = str(response['statevalue'])
    
    if val == TELLSTICK_TURNON:
        state = 'ON'
    elif val == TELLSTICK_TURNOFF:
        state = 'OFF'
    elif val == TELLSTICK_DIM:
        state = val2
    elif val == TELLSTICK_UP:
        state = "UP"
    elif val == TELLSTICK_DOWN:
        state = "DOWN"
    else:
        state = 'Unknown state'
    
    return state


def switchRpiOff():
    doMethod(SALON_ID, TELLSTICK_TURNOFF)


def doMethod(deviceId, methodId, methodValue=0):
    response = doRequest('device/info', {'id': deviceId})
    
    if methodId == TELLSTICK_TURNON:
        method = 'on'
    elif methodId == TELLSTICK_TURNOFF:
        method = 'off'
    elif methodId == TELLSTICK_BELL:
        method = 'bell'
    elif methodId == TELLSTICK_UP:
        method = 'up'
    elif methodId == TELLSTICK_DOWN:
        method = 'down'
    elif methodId == TELLSTICK_DIM:
        method = 'dim'
    
    if 'error' in response:
        name = ''
        retString = response['error']
    else:
        name = response['name']
        response = doRequest('device/command', {'id': deviceId, 'method': methodId, 'value': methodValue})
        if 'error' in response:
            retString = response['error']
        else:
            retString = response['status']
    
    if methodId in (TELLSTICK_TURNON, TELLSTICK_TURNOFF):
        # print ("Turning %s device %s, %s - %s" % (method, deviceId, name, retString))
        return retString
    elif methodId in (TELLSTICK_BELL, TELLSTICK_UP, TELLSTICK_DOWN):
        # print("Sending %s to: %s %s - %s" % (method, deviceId, name, retString))
        return retString
    elif methodId == TELLSTICK_DIM:
        # print ("Dimming device: %s %s to %s - %s" % (deviceId, name, methodValue, retString))
        return retString


def doRequest(method, params):
    consumer = oauth.OAuthConsumer(PUBLIC_KEY, PRIVATE_KEY)
    
    token = oauth.OAuthToken(TOKEN, TOKEN_SECRET)
    
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_method='GET',
                                                               http_url="http://api.telldus.com/json/" + method,
                                                               parameters=params)
    oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), consumer, token)
    headers = oauth_request.to_header()
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    
    conn = httplib.HTTPConnection("api.telldus.com:80")
    conn.request('GET', "/json/" + method + "?" + urllib.urlencode(params, True).replace('+', '%20'), headers=headers)
    response = conn.getresponse()
    return json.load(response)
