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
from urllib import urlencode, unquote_plus
import urllib2
import xml.dom.minidom
import logging
from arcs.gsi.certificate import CertificateRequest
from M2Crypto import X509

log = logging.getLogger('slick-client')


def parse_slcsResponse(response):
    """
    <?xml version="1.0" ?>
    <SLCSLoginResponse>
    <Status>Success</Status>
    <AuthorizationToken>EKJH54HJKRT908YSEDJNQ23QLIUYIU2HWQWDB12IEGB12DAIKJAAPQ1</AuthorizationToken>
    <CertificateRequest url="https://slcs1.arcs.org.au:443/SLCS/certificate">
    <Subject>DC=slcs,DC=org,DC=au,O=Org,CN=Common Name Dlw349sKRMWOsokaA</Subject>
    <CertificateExtension critical="false" name="ExtendedKeyUsage" oid="2.5.29.37">ClientAuth</CertificateExtension>
    <CertificateExtension critical="true" name="KeyUsage" oid="2.5.29.15">DigitalSignature,KeyEncipherment</CertificateExtension>
    <CertificateExtension critical="false" name="CertificatePolicies" oid="2.5.29.32">1.3.6.1.4.1.31863.1.0.1</CertificateExtension>
    <CertificateExtension critical="false" name="SubjectAltName" oid="2.5.29.17">email:user@host.localdomain</CertificateExtension>
    </CertificateRequest>
    </SLCSLoginResponse>

    """
    slcsRespDOM = xml.dom.minidom.parse(response)

    token = slcsRespDOM.getElementsByTagName("AuthorizationToken")[0]\
                       .childNodes[0].data
    dn = slcsRespDOM.getElementsByTagName("Subject")[0].childNodes[0].data
    reqURL = slcsRespDOM.getElementsByTagName("CertificateRequest")[0]\
                        .getAttribute('url')
    elements = []
    for e in slcsRespDOM.getElementsByTagName('CertificateExtension'):
        name = str(e.getAttribute('name'))
        critical = str(e.getAttribute('critical')) == 'true' or False
        value = str(e.childNodes[0].data)
        elements.append({'name':name, 'critical':critical, 'value':value})
    return token, dn, reqURL, elements


def parse_slcsCertResponse(response):
    dom = xml.dom.minidom.parse(response)
    status = dom.getElementsByTagName("Status")[0].childNodes[0].data
    if status == 'Error':
        error = dom.getElementsByTagName("Error")[0].childNodes[0].data
        stack = dom.getElementsByTagName("StackTrace")[0].childNodes[0].data
        log.error(error)
        log.error(stack)
        return

    cert = dom.getElementsByTagName("Certificate")[0].childNodes[0].data
    return cert


def slcs(slcsResp):
    token, dn, reqURL, elements = parse_slcsResponse(slcsResp)

    certreq = CertificateRequest(dn=str(dn), extensions=elements)
    certreq.sign()
    # POST the Token and CertReq back to the slcs server
    data = urlencode({'AuthorizationToken': token,
                      'CertificateSigningRequest': repr(certreq)})
    log.info('Request Signing by SLCS')
    log.debug('POST: %s' % reqURL)
    certResp = urllib2.urlopen(reqURL, data)
    cert = parse_slcsCertResponse(certResp)
    return certreq.get_key(), certreq.get_pubkey(), X509.load_cert_string(str(cert),X509.FORMAT_PEM)

