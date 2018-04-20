#!/usr/bin/env python

import requests
import json
import logging
from f5.bigip import ManagementRoot
from f5.bigip.contexts import TransactionContextManager
import os
import sys
import time

# slurp credentials
with open('../f5deploy/config/creds.json', 'r') as f:
    config = json.load(f)
f.close()

f5_hosts = config['f5host']
f5_user = config['f5acct']
f5_password = config['f5pw']

# Logging
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
# Try to as closely match acme.sh log formatting as possible.
formatter = logging.Formatter('[%(asctime)s] %(message)s ','%c')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)
logger.propagate = False

requests.packages.urllib3.disable_warnings()

def deploy_cert(domain):

    logger.info('Deploying to {0} device(s)'.format(len(f5_hosts)))
    key = '{0}.key'.format(domain)
    cert = '{0}.cer'.format(domain)
    chain = 'fullchain.cer'

    for target_host in f5_hosts:
      mr = ManagementRoot(target_host, f5_user, f5_password)

      # Upload files
      mr.shared.file_transfer.uploads.upload_file(os.path.join(os.getcwd(),key))
      mr.shared.file_transfer.uploads.upload_file(os.path.join(os.getcwd(),cert))
      mr.shared.file_transfer.uploads.upload_file(os.path.join(os.getcwd(),chain))

      # Check to see if these already exist
      key_status = mr.tm.sys.file.ssl_keys.ssl_key.exists(
          name='{0}.key'.format(domain))
      cert_status = mr.tm.sys.file.ssl_certs.ssl_cert.exists(
          name='{0}.crt'.format(domain))
      chain_status = mr.tm.sys.file.ssl_certs.ssl_cert.exists(
          name='{0}.le-chain.crt'.format(domain))

      if key_status and cert_status and chain_status:

          # Certificate, Chain, and Key exist, we will modify them in a transaction
          tx = mr.tm.transactions.transaction
          with TransactionContextManager(tx) as api:

              modkey = api.tm.sys.file.ssl_keys.ssl_key.load(
                  name='{0}.key'.format(domain))
              modkey.sourcePath = 'file:/var/config/rest/downloads/{0}'.format(
                  key)
              modkey.update()

              modcert = api.tm.sys.file.ssl_certs.ssl_cert.load(
                  name='{0}.crt'.format(domain))
              modcert.sourcePath = 'file:/var/config/rest/downloads/{0}'.format(
                  cert)
              modcert.update()

              modchain = api.tm.sys.file.ssl_certs.ssl_cert.load(
                  name='{0}.le-chain.crt'.format(domain))
              modchain.sourcePath = 'file:/var/config/rest/downloads/{0}'.format(
                  chain)
              modchain.update()

              logger.info(
                "Existing Certificate for {0} updated.".format(domain))

      else:
          newkey = mr.tm.sys.file.ssl_keys.ssl_key.create(
              name='{0}.key'.format(domain),
              sourcePath='file:/var/config/rest/downloads/{0}'.format(
                  key))
          newcert = mr.tm.sys.file.ssl_certs.ssl_cert.create(
              name='{0}.crt'.format(domain),
              sourcePath='file:/var/config/rest/downloads/{0}'.format(
                  cert))
          newchain = mr.tm.sys.file.ssl_certs.ssl_cert.create(
              name='{0}.le-chain.crt'.format(domain),
              sourcePath='file:/var/config/rest/downloads/{0}'.format(
                  chain))
          logger.info(
              "Certificate, Key and Chain deployed for {0}.".format(domain))

      # Create SSL Profile if necessary
      if not mr.tm.ltm.profile.client_ssls.client_ssl.exists(
             name='cssl.{0}'.format(domain), partition='Common'):
          cssl_profile = {
              'name': '/Common/cssl.{0}'.format(domain),
              'cert': '/Common/{0}.crt'.format(domain),
              'key': '/Common/{0}.key'.format(domain),
              'chain': '/Common/{0}.le-chain.crt'.format(domain),
              'defaultsFrom': '/Common/clientssl'
          }
          mr.tm.ltm.profile.client_ssls.client_ssl.create(**cssl_profile)


def main(argv):
    """
    Main entrypoint.
    Can be accessed either through acme.sh deploy (called via an sh script) or
    through --renew-hook.

    When called by --deploy it will be passed 5 arguments representing domain
    and paths to certificates. argv[0] represents the renewed domain, which can
    be used to derive all certificate paths.

    When called by --renew-hook no arguments are passed, however os.cwd()
    returns the path to the domain's certificates. Basename represents the
    renewed domain.

    For F5 SSL cert deployment purposes the full list of domains on the
    certificate does not matter.

    """
    domain = argv[0] if argv else os.path.basename(os.getcwd())

    logger.info("Deploying to F5 for {0}".format(domain))
    deploy_cert(domain)

if __name__ == '__main__':
    main(sys.argv[1:])
