##############################################################################
#
# Copyright (c) 2009 Victorian Partnership for Advanced Computing Ltd and
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

import urllib2, urllib, cookielib
from HTMLParser import HTMLParser
from urllib2 import HTTPCookieProcessor, HTTPRedirectHandler, urlparse
from urllib2 import HTTPBasicAuthHandler
import logging
import re


log = logging.getLogger('slick-client')


class SmartRedirectHandler(HTTPRedirectHandler, HTTPBasicAuthHandler, HTTPCookieProcessor):

    def __init__(self, credentialmanager=None, **kwargs):
        HTTPBasicAuthHandler.__init__(self)
        HTTPCookieProcessor.__init__(self, **kwargs)
        self.credentialmanager = credentialmanager

    def http_error_302(self, req, fp, code, msg, headers):
        log.debug("GET %s" % req.get_full_url())
        result = HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.status = code
        return result

    http_error_301 = http_error_303 = http_error_307 = http_error_302

    def http_error_401(self, req, fp, code, msg, headers):
        url = req.get_full_url()
        authline = headers.getheader('www-authenticate')
        authobj = re.compile(
            r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',
            re.IGNORECASE)
        matchobj = authobj.match(authline)
        realm = matchobj.group(2)
        self.credentialmanager.print_realm(realm)
        user = self.credentialmanager.get_username()
        self.credentialmanager.set_password()
        passwd = self.credentialmanager.get_password()
        self.add_password(realm=realm, uri=url, user=user, passwd=passwd)
        return self.http_error_auth_reqed('www-authenticate',
                                          url, req, headers)



class FormParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_title = False
        self.in_form = False
        self.in_origin = False
        self.title = ''
        self.forms = []
        self.data = {}

    def handle_starttag(self, tag, attrs):
        self.origin_idp = None
        if tag == "title":
            self.in_title = True
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
        if self.in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "form":
            self.in_form = False
            self.forms.append(self.data)
        if self.in_form and self.in_origin and tag == "select":
            self.in_origin = False


def submitWayfForm(idp, opener, data, res):
    headers = {
    "Referer": res.url
    }
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


def submitIdpForm(opener, title, data, res, cm):
    headers = {
    "Referer": res.url
    }
    idp_data = {}
    url = urlparse.urljoin(res.url, data['form']['action'])
    log.info("Form Authentication from: %s" % url)
    cm.print_realm(title)
    idp_data['j_username'] = cm.get_username()
    cm.set_password()
    idp_data['j_password'] = cm.get_password()
    data = urllib.urlencode(idp_data)
    request = urllib2.Request(url, data=data)
    log.info('Submitting login form')
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


def whatForm(forms):
    form_types = {'wayf': ['origin', 'providerId', 'shire', 'target', 'time'],
                  'login': ['j_password', 'j_username'],
                  'idp': ['SAMLResponse', 'TARGET'],
    }

    def match_form(form, type, items):
        for i in items:
            if i not in form.keys():
                rtype = None
                rform = None
                break
            rtype = type
            rform = form
        return rtype, rform

    for form in forms:
        for ft in form_types:
            rtype,rform = match_form(form, ft, form_types[ft])
            if rtype:
                return rtype,rform
    return None, None


def run(idp, spURL, cm):
    cookiejar = cookielib.CookieJar()
    opener = urllib2.build_opener(SmartRedirectHandler(credentialmanager=cm, cookiejar=cookiejar))
    request = urllib2.Request(spURL)
    log.debug("GET: %s" % request.get_full_url())
    response = opener.open(request)

    slcsresp = None
    tries = 0
    while(not slcsresp):
        parser = FormParser()
        for line in response:
            parser.feed(line)
        parser.close()
        type, form = whatForm(parser.forms)
        if type == 'wayf':
            log.info('Submitting form to wayf')
            request, response = submitWayfForm(idp, opener, form, response)
            continue
        if type == 'login':
            if tries > 2:
                raise Exception("Too Many Failed Attempts to Authenticate")
            request, response = submitIdpForm(opener, parser.title, form, response, cm)
            tries += 1
            continue
        if type == 'idp':
            log.info('Submitting IdP SAML form')
            request, response = submitFormToSP(opener, form, response)
            return response
        raise("Uknown error: Shibboleth auth chain lead to nowhere")


def list_idps(spURL):
    opener = urllib2.build_opener(SmartRedirectHandler())
    request = urllib2.Request(spURL)
    log.debug("GET: %s" % request.get_full_url())
    response = opener.open(request)
    parser = FormParser()
    for line in response:
        parser.feed(line)
    type, form = whatForm(parser.forms)
    if type == 'wayf':
        return form['origin']
    raise("Uknown error: Shibboleth auth chain lead to nowhere")


