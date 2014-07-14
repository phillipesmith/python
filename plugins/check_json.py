#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# Author:  Phillipe Smith <phillipelnx@gmail.com>
# Date:    08/07/2014
# License: GPL
# Version: 1.1
#
# The checks verifies a JSON url result and generates a Nagios compatible service with the results
#
# Check options:
#     -h  Help message
#     -u  URL with JSON rsult
#     -f  Regular expression for filter only determined results
#     -p  Generates perfdata. Need 
#
# Example of output gerenerated:
#     $./check_json.py -u http://date.jsontest.com/
#      JSON Status API OK - date: 07-12-2014, milliseconds_since_epoch: 1405126483908, time: 12:54:43 AM
#
# TODO:
#     Remove the limit of 4 levels for JSON configuration tree
#     Add Warning and Critical configuration
#

import json
import sys
import re
from optparse import OptionParser
from urllib2 import urlopen, Request, URLError, HTTPError

parser = OptionParser(usage='usage: %prog [ -u|--url http://json_result_url ] [ -f|--filter filter_expression ] [ -p|--perfdata ]')
parser.add_option('-u', '--url', dest='url', help='JSON api url')
parser.add_option('-f', '--filter', dest='filter', default='', help='Filter determined values. Ex.: "^tcp|^udp"')
parser.add_option('-p', '--perfdata', dest='perfdata', default=False, help='Enable performance data. Must specify a expression with the values that going to be used as perfdata. If you want to show all values as perfdata put a "."')

(option, args) = parser.parse_args()

# Nagios status and messages
nagios_status = ['OK', 'WARNING', 'CRITICAL', 'UNKNOW']

filter   = option.filter
perfdata = option.perfdata
textinfo = []


def exit(status, message):
    print 'JSON Status API %s - %s' % (nagios_status[int(status)], message)
    sys.exit(status)

def output(data):
    message_list = []
    perf = []

    for level1, value in data.items():
        if isinstance(value, dict):
            for level2, value in value.items():
                if isinstance(value, dict):
                    for level3, value in value.items():
                        if isinstance(value, dict):
                            for level4, value in value.items():
                                textinfo.append('%s.%s.%s.%s: %s' % (level1, level2, level3, level4, value))
                        else:
                            textinfo.append('%s.%s.%s: %s' % (level1, level2, level3, value))
                else:
                    textinfo.append('%s.%s: %s' % (level1, level2, value))
        else:
            textinfo.append('%s: %s' % (level1, value))

    for value in textinfo:        
        if re.search(filter, value, re.IGNORECASE):
            message_list.append(value)
            if perfdata and re.search(perfdata, value):
                perf.append(value.replace(': ', '='))

    if not message_list:
        exit(3, 'No value information with the filter specified.')

    
    message = ', '.join(sorted(message_list))
    perf    = ';; '.join(sorted(perf))

    if perf:                
        return exit(0, message + ' | ' + perf)
    else:        
        return exit(0, message)

if not option.url:
    exit(3, 'Missing command line arguments')

try:
    request  = Request(option.url)
    response = urlopen(request)
except URLError as err:
    exit(3, 'Url request error. %s' % err)
except HTTPError as err:
    exit(3, 'Invalid Uri. %s' % err.reason)
else:
    try:
        json_response = json.loads(response.read().decode('iso-8859-1'))
    except Exception, e:
        exit(3, 'Invalid JSON response. %s' % e)

if isinstance(json_response, list):
    for item in json_response:        
        print output(item)
else:
    print output(json_response)

