##############################################################################
#
# Copyright (c) 2009 James Cook University and Contributors.
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

keyUsage = { 'DigitalSignature' : 'Digital Signature',
            'KeyEncipherment' : 'Key Encipherment',
           }

extendedKeyUsage = { 'ClientAuth' : 'clientAuth',
           }


def slcs(slcsResp, SLCS_URL):
    slcsRespDOM = xml.dom.minidom.parse(slcsResp)

    token = slcsRespDOM.getElementsByTagName("AuthorizationToken")[0].childNodes[0].data
    dn = slcsRespDOM.getElementsByTagName("Subject")[0].childNodes[0].data
    reqURL = slcsRespDOM.getElementsByTagName("CertificateRequest")[0].childNodes[0].data


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
    for e in slcsRespDOM.getElementsByTagName('CertificateExtension'):
        name = str(e.getAttribute('name'))
        critical = str(e.getAttribute('critical')) == 'true' or False
        if name.lower() == 'keyusage':
            value = ', '.join([keyUsage[v] for v in e.childNodes[0].data.split(',')])
            extstack.push(X509.new_extension(Att_map[name.lower()], value,
                                             critical=int(critical)))
        elif name.lower() == 'extendedkeyusage':
            value = ', '.join([extendedKeyUsage[v] for v in e.childNodes[0].data.split(',')])
            extstack.push(X509.new_extension(Att_map[name.lower()], value,
                                             critical=int(critical)))
        else:
            extstack.push(X509.new_extension(Att_map[name.lower()],
                                             str(e.childNodes[0].data),
                                             critical=int(critical)))
    req.add_extensions(extstack)
    req.sign(pubKey, 'sha1')

    # POST the Token and CertReq back to the slcs server
    data = urlencode({'AuthorizationToken':token,'CertificateSigningRequest':req.as_pem()})
    log.info('Request Signing by SLCS')
    log.debug('POST: %s' % SLCS_URL)
    certResp = urllib2.urlopen(SLCS_URL, data)
    certRespDOM = xml.dom.minidom.parse(certResp)
    status = certRespDOM.getElementsByTagName("Status")[0].childNodes[0].data
    if status == 'Error':
        error = certRespDOM.getElementsByTagName("Error")[0].childNodes[0].data
        stack = certRespDOM.getElementsByTagName("StackTrace")[0].childNodes[0].data
        log.error(stack)
        return
        #return ('Error - %s' % error, '<h1>%s</h1><pre>%s</pre>' % (error, stack))

    #from ipdb import set_trace; set_trace()
    cert = certRespDOM.getElementsByTagName("Certificate")[0].childNodes[0].data
    return key.as_pem(cipher=None), X509.load_cert_string(str(cert),X509.FORMAT_PEM).as_text()
