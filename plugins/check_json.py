#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# Author:  Phillipe Smith <phillipelnx@gmail.com>
# Date:    08/07/2014
# License: GPL
# 
# The checks verifies a JSON url result and generates a Nagios compatible service with the results
# 
# Check options:
#     -h  Help message
#     -u  URL with JSON rsult
#     -f  Regular expression for filter only determined results
#     -p  Generates perfdata
#
# Example of output gerenerated:
#     $./check_json.py -u http://ntop.host.example/lua/host_get_json.lua?host=10.1.1.5 -f '^tcp'
#      JSON Status API OK - tcp_sent.mbits: 132, tcp_sent.packets: 96155, tcp_rcvd.mbits: 5881, tcp_rcvd.packets: 85115809 | tcp_sent.mbits=132;; tcp_sent.packets=96155;; tcp_rcvd.mbits=5881;; tcp_rcvd.packets=85115809

import json
import sys
import re
from optparse import OptionParser
from urllib2 import urlopen, Request, URLError, HTTPError

parser = OptionParser(usage='usage: %prog -H hostname/ip [-f filter_expression]')
parser.add_option('-u', '--url', dest='url', help='JSON api url')
parser.add_option('-f', '--filter', dest='filter', default='', help='Filter determined values. Ex.: "^tcp|^udp"')
parser.add_option('-p', '--perfdata', dest='perfdata', action='store_true', help='Enable performance data')

(option, args) = parser.parse_args()

# Nagios status and messages
ok       = (0, 'OK')
warning  = (1, 'WARNING')
critical = (2, 'CRITICAL')
unknown  = (3, 'UNKNOW')

filter   = option.filter
request  = Request(option.url)
perfdata = option.perfdata
textinfo = []

def exit(status, message):
    print 'JSON Status API %s - %s' % (status[1], message)
    sys.exit(status[0])

def output(message):
    message_list = []
    perf = []

    for value in message:
        if re.search(filter, value, re.IGNORECASE):
            if 'bytes' in value:
                item = value.split(':')
                mbits = int(item[1]) / 1024 / 1024 
                value = '%s: %s' % (item[0].replace('bytes','mbits'), mbits)

            message_list.append(value)
            perf.append(value.replace(': ', '='))

    if not message_list:
        exit(unknown, 'Invalid filter passed.')

    if perfdata: 
        return 'JSON Status API %s - %s | %s' % (ok[1], ', '.join(message_list), ';; '.join(perf))
    else:
        return 'JSON Status API %s - %s' % (ok[1], ', '.join(message_list))

if not request:
    exit(unknown, 'Missing command line arguments')

try:
    response = urlopen(request)
except URLError as e:
    exit(critical, 'Url request returning: ' + e.code)
except HTTPError as e:
    exit(unknown, 'Invalid Uri. %s' % e.reason)
else:
    try:
        json_response = json.loads(response.read())
    except Exception, e:
        exit(critical, 'Invalid JSON response. %s' % e)

for key in json_response:
    if isinstance(json_response[key], dict):
        for value in json_response[key]:
            if isinstance(json_response[key][value], dict):
                for item in json_response[key][value]:
                    if isinstance(json_response[key][value][item], dict):
                        for subitem in json_response[key][value][item]:
                            textinfo.append('%s.%s.%s.%s: %s' % (key, value, item, subitem, json_response[key][value][item][subitem]))
                    else:
                        textinfo.append('%s.%s.%s: %s' % (key, value, item, json_response[key][value][item]))
            else:
                textinfo.append('%s.%s: %s' % (key, value, json_response[key][value]))
    else:
        textinfo.append('%s: %s' % (key, json_response[key]))

print output(textinfo)
