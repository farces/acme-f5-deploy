#!/usr/bin/env python

import json
import logging
from f5.bigip import ManagementRoot
from f5.bigip.contexts import TransactionContextManager
import os
import sys

# slurp credentials
cfg_file = os.path.join(sys.path[0], "config/creds.json")
with open(cfg_file, 'r') as f:
    config = json.load(f)
f.close()

f5_hosts = config['f5host']
f5_user = config['f5acct']
f5_password = config['f5pw']

# Logging
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(message)s ', '%c')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)
logger.propagate = False


def deploy_cert(domain,path):
    logger.info('Deploying to {0} device(s)'.format(len(f5_hosts)))
    key = '{0}.key'.format(domain)
    cert = '{0}.cer'.format(domain)
    chain = 'fullchain.cer'

    for target_host in f5_hosts:
        mr = ManagementRoot(target_host, f5_user, f5_password)

        # Shorten API calls
        mr_upload_file = mr.shared.file_transfer.uploads.upload_file
        mr_cert_create = mr.tm.sys.file.ssl_certs.ssl_cert.create
        mr_key_create = mr.tm.sys.file.ssl_keys.ssl_key.create
        mr_key_exists = mr.tm.sys.file.ssl_keys.ssl_key.exists
        mr_cert_exists = mr.tm.sys.file.ssl_certs.ssl_cert.exists

        # Upload files
        mr_upload_file(os.path.join(path, key))
        mr_upload_file(os.path.join(path, cert))
        mr_upload_file(os.path.join(path, chain))

        # Check to see if these already exist
        key_status = mr_key_exists(name='{0}.key'.format(domain))
        cert_status = mr_cert_exists(name='{0}.crt'.format(domain))
        chain_status = mr_cert_exists(name='{0}.le-chain.crt'.format(domain))

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
            mr_key_create(
                name='{0}.key'.format(domain),
                sourcePath='file:/var/config/rest/downloads/{0}'.format(key))
            mr_cert_create(
                name='{0}.crt'.format(domain),
                sourcePath='file:/var/config/rest/downloads/{0}'.format(cert))
            mr_cert_create(
                name='{0}.le-chain.crt'.format(domain),
                sourcePath='file:/var/config/rest/downloads/{0}'.format(chain))
            logger.info(
                "Certificate, Key and Chain deployed for {0}.".format(domain))

        # Create SSL Profile if it does not already exist
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
    """
    domain = os.path.basename(os.getcwd())
    if not domain:
      # Called from --deploy-hook, create domain and path from argv
      logger.info("Deploying from --deploy-hook")
      domain = argv[0]
      path = os.path.dirname(argv[1])
    else:
      # Called from --renew-hook, create domain and path from cwd
      logger.info("Deploying from --renew-hook")
      path = os.getcwd()

    logger.info("Deploying to F5 for {0}".format(domain))
    deploy_cert(domain,path)

if __name__ == '__main__':
    main(sys.argv[1:])