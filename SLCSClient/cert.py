##############################################################################
#
# Copyright (c) 2009 Victorian Partnership for Advanced Computing and
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
from M2Crypto import X509, RSA, EVP, m2
import xml.dom.minidom
import logging

log = logging.getLogger('slcs-client')

MBSTRING_ASC  = 0x1000 | 1

Att_map = {'extendedkeyusage': 'extendedKeyUsage',
           'keyusage': 'keyUsage',
           'certificatepolicies': 'certificatePolicies',
           'subjectaltname': 'subjectAltName',
          }

multi_attrs ={ 'keyusage': { 'digitalsignature' : 'Digital Signature',
                            'keyencipherment' : 'Key Encipherment',
                           }
              , 'extendedkeyusage' : { 'clientauth' : 'clientAuth', }
             }

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

    token = slcsRespDOM.getElementsByTagName("AuthorizationToken")[0].childNodes[0].data
    dn = slcsRespDOM.getElementsByTagName("Subject")[0].childNodes[0].data
    reqURL = slcsRespDOM.getElementsByTagName("CertificateRequest")[0].getAttribute('url')
    elements = []
    for e in slcsRespDOM.getElementsByTagName('CertificateExtension'):
        name = str(e.getAttribute('name'))
        critical = str(e.getAttribute('critical')) == 'true' or False
        if name.lower() in multi_attrs:
            value = ', '.join([multi_attrs[name.lower()][v.lower()]
                               for v in e.childNodes[0].data.split(',')])
        else:
            value = str(e.childNodes[0].data)
        elements.append({'name':name, 'critical':critical, 'value':value})
    return token, dn, reqURL, elements


def generate_certificate(dn, elements):

    # Generate keys
    log.info('Generating Key')
    key = RSA.gen_key(2048, m2.RSA_F4)

    # Create public key object
    pubKey = EVP.PKey()
    pubKey.assign_rsa(key)

    log.info('Generating Certificate Request')
    req = X509.Request()

    # Add the public key to the request
    req.set_version(0)
    req.set_pubkey(pubKey)

    # Set DN
    x509Name = X509.X509_Name()
    for entry in dn.split(','):
        l = entry.split("=")
        x509Name.add_entry_by_txt(field=str(l[0].strip()), type=MBSTRING_ASC,
                                      entry=str(l[1]),len=-1, loc=-1, set=0)

    req.set_subject_name(x509Name)

    extstack = X509.X509_Extension_Stack()
    for e in elements:
        name = e['name']
        critical = e['critical']
        extstack.push(X509.new_extension(Att_map[name.lower()],
                                         e['value'],
                                         critical=int(critical)))
    req.add_extensions(extstack)
    req.sign(pubKey, 'sha1')

    return (key, req, pubKey)

def parse_slcsCertResponse(certResp):
    certRespDOM = xml.dom.minidom.parse(certResp)
    status = certRespDOM.getElementsByTagName("Status")[0].childNodes[0].data
    if status == 'Error':
        error = certRespDOM.getElementsByTagName("Error")[0].childNodes[0].data
        stack = certRespDOM.getElementsByTagName("StackTrace")[0].childNodes[0].data
        log.error(stack)
        return
        #return ('Error - %s' % error, '<h1>%s</h1><pre>%s</pre>' % (error, stack))

    cert = certRespDOM.getElementsByTagName("Certificate")[0].childNodes[0].data
    return cert


def slcs(slcsResp):
    token, dn, reqURL, elements = parse_slcsResponse(slcsResp)

    key, req, pubKey = generate_certificate(dn, elements)

    # POST the Token and CertReq back to the slcs server
    data = urlencode({'AuthorizationToken':token,'CertificateSigningRequest':req.as_pem()})
    log.info('Request Signing by SLCS')
    log.debug('POST: %s' % reqURL)
    certResp = urllib2.urlopen(reqURL, data)
    cert = parse_slcsCertResponse(certResp)
    return key.as_pem(cipher=None), X509.load_cert_string(str(cert),X509.FORMAT_PEM).as_text()

