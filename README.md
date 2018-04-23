# acme-f5-deploy
Python script to deploy &amp; renew certificates from LetsEncrypt to an F5 BIG-IP system. Certificates generated by acme.sh, with Client SSL profiles created using the F5 python SDK. Designed to run as a renew hook, but can be used as a deploy hook if you like.

Tested against BIGIP v13.

A bit rough around the edges.

Repo includes a modified Dockerfile to include python, pip and f5-sdk.

## Usage
`This has primarily been tested using Docker, but should work fine without`
1. Build docker image:
`docker build -t acme_f5 .`
2. Copy the config and f5deploy directories into the root directory for acme.sh (in these examples it is `$(pwd)/out`)
3. `chmod +x $(pwd)/out/f5deploy/f5deploy.py`
4. Modify creds.json to include the F5 hosts to deploy certificates to (may be multiple) and credentials - credentials are the same for all hosts.
5. Launch acme.sh in docker with the deployment script as --renew-hook target
  ```
  docker run --rm  -it  \
 -v "$(pwd)/out":/acme.sh  \
 acme_f5 --issue -d xyz.domain.com \ 
 --renew-hook "/acme.sh/f5deploy/f5deploy.py"
  ```
6. Force renew the certificate
  ```
  docker run --rm  -it  \
  -v "$(pwd)/out":/acme.sh  \
  acme_f5 --renew -d xyz.domain.com --force
  ```
  
At this stage the script should run and successfully create certificates, keys, chains and profiles on the F5 appliances ready for use.

On first run the certificates aren't pushed to the F5 - this is a shortcoming in acme.sh where a certificate issuance isn't considered a renewal, and there is no reliable way to trigger the script only on renew success that I can see. 
An alternative to forcing a renew is to cd to the `out/xyz.domain.com` directory and run `../f5deploy/f5deploy.py xyz.domain.com` manually. This only needs to be done once for each certificate.

This works correctly for all use cases found at https://github.com/Neilpang/acme.sh/wiki/Run-acme.sh-in-docker including daemon, which will automatically renew and push changes to the F5.
**If running as daemon with --restart=unless-stopped (or equivalent), do not use -v $(pwd)/out as this won't be correct on restart - use the full path to the out/ directory instead.**
## Configuration
All configuration is in config/creds.json.
```
{
  "f5host": [
    "1.2.3.4",
    "2.3.4.5"
  ],
  "f5acct": "admin",
  "f5pw": "admin"
}
```
f5host: may be a single IP address, or multiple separated by commas.
f5acct and f5pw are shared for all hosts at this stage.

## acme.sh --deploy
*If you're using docker with the included Dockerfile, the deploy script is copied automatically during build.*
If you're not using docker you will need to copy `f5deploy.sh` to the deploy directory of acme.sh.

You can then run `acme.sh --deploy -d xyz.domain.com --deploy-hook f5deploy`

For Docker you would use:
```
docker run --rm  -it  \
-v "$(pwd)/out":/acme.sh  \
acme_f5 --deploy -d xyz.domain.com \ 
--deploy-hook f5deploy
```
**NOTE: When doing --deploy with a --deploy-hook the hook is stored permanently in the xyz.domain.com.conf file. 
If you also set a --renew-hook during --issue, it will store both and run both on-renewal, which shouldn't cause problems but is not ideal.**
*acme.sh* does not have a --deploy-hook method that only runs on successful renewal currently.

At this time I'd recommend using the --renew-hook and doing a --renew --force the first time, rather than using the --deploy-hook. If you opt for the deploy hook script don't also use the --renew-hook parameter. 

## acme.sh daemon
If running as a daemon in docker and --restart is set to true (or any value that would allow a restart) you will need to use `-v "/full/path/to/out:/acme.sh"`. When the container restarts it does not maintain the original $(pwd). This is a docker peculiarity.

## Notes
On the F5 the following is created:
- Certificate & Key: xyz.domain.com
- Chain: xyz.domain.com.le-chain - this includes both the domain certificate and LetsEncrypt Authority.
- Client SSL Profile: cssl.xyz.domain.com. This profile is never overwritten and can be customized as required.

## Credits
@f5central for the API script modified from https://github.com/f5devcentral/lets-encrypt-python
