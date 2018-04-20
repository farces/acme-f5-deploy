# acme-f5-deploy
Python script to deploy &amp; renew certificates and profiles using F5 API

## Usage
`This has primarily been tested using Docker, but should work fine without`
1. Build docker image:
`docker build -t acme_f5 .`
2. Move all files from this repository into the root directory for acme.sh (in these examples it is $(pwd)/out/)
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
  
At this stage the script should run and successfully create certificates, keys, chains and profiles on the F5 appliances.

On first run the certificates aren't pushed to the F5 - this is a shortcoming in acme.sh where a certificate issuance isn't considered a renewal, and there is no other way to trigger the script. An alternative to forcing a renew is to cd to the out/xyz.domain.com directory and run `../f5deploy/f5deploy.py xyz.domain.com`. This only needs to be done once.

This works correctly for all use cases found at https://github.com/Neilpang/acme.sh/wiki/Run-acme.sh-in-docker including daemon, which will automatically renew and push changes to the F5.

Credit to @f5central for the API script modified from https://github.com/f5devcentral/lets-encrypt-python
