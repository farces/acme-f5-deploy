# acme-f5-deploy
Python script to deploy &amp; renew certificates and profiles using F5 API

A bit rough around the edges.

Repo includes a modified Dockerfile to include python, pip and f5-sdk.

## Usage
`This has primarily been tested using Docker, but should work fine without`
1. Build docker image:
`docker build -t acme_f5 .`
2. Copy the config and f5deploy directories into the root directory for acme.sh (in these examples it is `$(pwd)/out`)
3. Modify creds.json to include the F5 hosts to deploy certificates to (may be multiple) and credentials - credentials are the same for all hosts.
4. Launch acme.sh in docker with the deployment script as --renew-hook target
  ```
  docker run --rm  -it  \
 -v "$(pwd)/out":/acme.sh  \
 acme_f5 --issue -d xyz.domain.com \ 
 --renew-hook "/acme.sh/f5deploy/f5deploy.py"
  ```
5. Force renew the certificate
  ```
  docker run --rm  -it  \
  -v "$(pwd)/out":/acme.sh  \
  acme_f5 --renew -d xyz.domain.com --force
  ```
  
At this stage the script should run and successfully create certificates, keys, chains and profiles on the F5 appliances ready for use.

On first run the certificates aren't pushed to the F5 - this is a shortcoming in acme.sh where a certificate issuance isn't considered a renewal, and there is no reliable way to trigger the script only on renew success that I can see. 
An alternative to forcing a renew is to cd to the `out/xyz.domain.com` directory and run `../f5deploy/f5deploy.py xyz.domain.com` manually. This only needs to be done once for each certificate.

This works correctly for all use cases found at https://github.com/Neilpang/acme.sh/wiki/Run-acme.sh-in-docker including daemon, which will automatically renew and push changes to the F5.

## Notes
On the F5 the following are created:
- Certificate & Key: xyz.domain.com
- Chain: xyz.domain.com.le-chain - this includes both the domain certificate and LetsEncrypt Authority.
- Client SSL Profile: cssl.xyz.domain.com

Configuration directory is hardcoded to ../f5deploy/config/ within the script - this is OK in the general case but may not be accurate if you have configured acme.sh to put certificates outside of the default location (or have the script and config elsewhere when not running under docker).

## Credits
@f5central for the API script modified from https://github.com/f5devcentral/lets-encrypt-python
