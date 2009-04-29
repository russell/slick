##############################################################################
#
# Copyright (c) 2009 Victorian Partnership for Advanced Computing and
# Contributors.
# All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import urllib2, httplib, HTMLParser, urllib, cookielib
from urllib2 import HTTPCookieProcessor, HTTPRedirectHandler, urlparse
from urllib2 import HTTPBasicAuthHandler, AbstractBasicAuthHandler, BaseHandler
from pprint import pprint
import logging

from getpass import getpass

log = logging.getLogger('slcs-client')
verbose = logging.getLogger('slcs-client-verbose')


class SmartRedirectHandler(HTTPRedirectHandler, HTTPBasicAuthHandler, HTTPCookieProcessor):

    def __init__(self, **kwargs):
        HTTPBasicAuthHandler.__init__(self)
        HTTPCookieProcessor.__init__(self, **kwargs)

    def http_error_301(self, req, fp, code, msg, headers):
        verbose.info("redirect")
        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        log.debug("GET %s" % req.get_full_url())
        verbose.info("redirect")
        result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.status = code
        return result

cookiejar = cookielib.CookieJar()
opener = urllib2.build_opener(SmartRedirectHandler(cookiejar=cookiejar))

class FormParser(HTMLParser.HTMLParser):
    in_form = False
    in_origin = False
    forms = []
    data = {}
    def handle_starttag(self, tag, attrs):
        self.origin_idp = None
        if tag == "form":
            if self.data:
                self.data = {}
            self.in_form = True
            self.data['form'] = dict(attrs)
        if self.in_form and tag == "select" and ('name','origin') in attrs:
            self.in_origin = True
            self.data['origin'] = {}
        if self.in_form and self.in_origin and tag == "option":
            self.origin_idp = attrs
        if self.in_form and tag == "input":
            attrs = dict(attrs)
            if 'name' in attrs:
                self.data[attrs['name']] = attrs
    def handle_data(self, data):
        if self.in_form and self.in_origin and self.origin_idp and data.strip():
            self.data['origin'][data.strip()] = self.origin_idp[0][1]

    def handle_endtag(self, tag):
        if tag == "form":
            self.in_form = False
            self.forms.append(self.data)
        if self.in_form and self.in_origin and tag == "select":
            self.in_origin = False


def submitWayfForm(idp, opener, data, res):
    headers = {
    "Referer": res.url
    }
    #httplib.HTTPConnection.debuglevel = 1
    #Set IDP to correct IDP
    wayf_data = {}
    wayf_data['origin'] = data['origin'][idp]
    wayf_data['shire'] = data['shire']['value']
    wayf_data['providerId'] = data['providerId']['value']
    wayf_data['target'] = data['target']['value']
    wayf_data['time'] = data['time']['value']
    wayf_data['cache'] = 'false'
    wayf_data['action'] = 'selection'
    url = urlparse.urljoin(res.url, data['form']['action'])
    data = urllib.urlencode(wayf_data)
    request = urllib2.Request(url + '?' + data)
    log.debug("POST: %s" % request.get_full_url())
    response = opener.open(request)
    return request, response


def submitIdpForm(opener, data, res):
    headers = {
    "Referer": res.url
    }
    idp_data = {}
    url = urlparse.urljoin(res.url, data['form']['action'])
    log.info("Form Authentication from: %s" % url)
    idp_data['j_username'] = raw_input("Username:")
    idp_data['j_password'] = getpass("Password:")
    data = urllib.urlencode(idp_data)
    request = urllib2.Request(url, data=data)
    log.debug("POST: %s" % request.get_full_url())
    response = opener.open(request)
    return request, response

def submitFormToSP(opener, data, res):
    headers = {
    "Referer": res.url
    }
    url = urlparse.urljoin(res.url, data['form']['action'])
    data = urllib.urlencode({'SAMLResponse':data['SAMLResponse']['value'], 'TARGET':'cookie'})
    request = urllib2.Request(url, data=data)
    log.debug("POST: %s" % request.get_full_url())
    response = opener.open(request)
    return request, response


def run(idp, spURL):
    cookiejar = cookielib.CookieJar()
    opener = urllib2.build_opener(SmartRedirectHandler(cookiejar=cookiejar))
    request = urllib2.Request(spURL)
    #httplib.HTTPConnection.debuglevel = 1
    log.debug("GET: %s" % request.get_full_url())
    response = opener.open(request)
    parser = FormParser()
    for line in response:
        parser.feed(line)
    parser.close()
    wayf_form = None
    error = "Error unable to parse wayf"
    for form in parser.forms:
        if form.has_key('origin'):
            error = "Error idp not in wayf"
            if idp in form['origin'].keys():
                wayf_form = form
                break
    if not wayf_form:
        return error
    request, response = submitWayfForm(idp, opener, wayf_form, response)
    parser = FormParser()
    for line in response:
        parser.feed(line)
    parser.close()
    request, response = submitIdpForm(opener, parser.data, response)
    for line in response:
        parser.feed(line)
    request, response = submitFormToSP(opener, parser.data, response)
    return response
    #opener.add_password(realm=realm, uri=uri, user=user, passwd=passwd)
    #from ipdb import set_trace; set_trace()


def list_idps(spURL):
    opener = urllib2.build_opener(SmartRedirectHandler())
    request = urllib2.Request(spURL)
    log.debug("GET: %s" % request.get_full_url())
    response = opener.open(request)
    parser = FormParser()
    for line in response:
        parser.feed(line)
    for form in parser.forms:
        if form.has_key('origin'):
            return form['origin']

