# acme-f5-deploy
Python script to deploy &amp; renew certificates from LetsEncrypt to an F5 BIG-IP system. Certificates generated by acme.sh, with Client SSL profiles created using the F5 python SDK. Designed to run as a renew hook, but can be used as a deploy hook if you like.

Tested against BIGIP v13.

A bit rough around the edges.

Repo includes a modified Dockerfile to include python, pip and f5-sdk.

## Quick Usage
`This has primarily been tested using Docker, but should work fine without`
1. `chmod +x configure.sh && ./configure.sh` (see Configuration section below for additional details)
2. Modify creds.json to include the F5 hosts to deploy certificates to (may be multiple) and credentials - credentials must be the same for all hosts.
3. Launch acme.sh in docker with the deployment script as `--renew-hook` target, or as a `--deploy-hook` target during a `--deploy` action.
  ```
  docker run --rm  -it  \
 -v "$(pwd)/out":/acme.sh  \
 acme_f5 --issue -d xyz.domain.com \ 
 --renew-hook "/acme.sh/f5deploy/f5deploy.py"
  ```
4. Force renew the certificate
  ```
  docker run --rm  -it  \
  -v "$(pwd)/out":/acme.sh  \
  acme_f5 --renew -d xyz.domain.com --force
  ```
  
At this stage the script should run and successfully create certificates, keys, chains and profiles on the F5 appliances ready for use.

On first run the certificates aren't pushed to the F5 - this is a shortcoming in acme.sh where a certificate issuance isn't considered a renewal, and there is no reliable way to trigger the script only on renew success that I can see. 
An alternative to forcing a renew is to cd to the `out/xyz.domain.com` directory and run `/path/to/f5deploy.py xyz.domain.com` manually. This only needs to be done once for each certificate.

This works correctly for all use cases found at https://github.com/Neilpang/acme.sh/wiki/Run-acme.sh-in-docker including daemon, which will automatically renew and push changes to the F5.
**If running as daemon with `--restart=unless-stopped` (or equivalent), do not use `-v $(pwd)/out` as this won't be correct on restart - use the full path to the out/ directory instead.**
## Configuration
All configuration is in config/creds.json.
```
{
  "f5host": [
    "192.168.1.92"
  ],
  "f5acct": "admin",
  "f5pw": "admin"
  "create_cssl": true,
  "f5partition": "Common",
  "parent_cssl": "/Common/clientssl"
}
```
* f5host: may be a single IP address, or multiple separated by commas.
* f5acct and f5pw: shared credentials for all hosts at this stage.
* create_cssl: boolean- create client SSL profile on F5 - default is true.
* f5partition: partition to crete CSSL in - default is Common. **Only include partition name without leading or trailing slashes.**
* parent_cssl: parent client SSL profile - default is /Common/clientssl. **Include full path including partition (may be different to f5partition if the profile is e.g. in /Common/ while the new profile will be in /Specific/**

If any of create_cssl, f5partition or parent_cssl are missing they will use their defaults.

### ./configure.sh
**Make sure you run `./configure.sh` from the directory you will be keeping the scripts - it will hardcode paths into f5deploy.sh that will require running `./configure.sh` again if f5deploy.py is moved.**

`./configure.sh` performs the following tasks:
- `chmod +x ./f5deploy/f5deploy.py`
- Replaces the path to the f5deploy.py script in f5deploy.sh with the full path to ./f5deploy/f5deploy.py
    - *f5deploy.sh.1* is created as a copy of the original file
- Copies f5deploy.sh to the directory specified in `--deploy-path <path>`
- Builds the acme_f5 docker image, including the modified *f5deploy.sh*
    - This can be disabled with `--nodocker`
    
This was kept outside of the Dockerfile for support of non-Docker configurations.

### f5deploy.sh
This script now tests for if it's running inside or outside of Docker, and launches the f5deploy.py script correctly based on this. `./configure.sh` does the work in setting the correct path.

You can now use `--deploy-hook` more confidently in place of `--renew-hook`.

## acme.sh --deploy
*If you're using docker with the included Dockerfile, the deploy script is copied automatically during build.*
If you're not using docker you can run `./configure.sh --nodocker --deploy-path /path/to/.acme.sh/deploy/

You can then run `acme.sh --deploy -d xyz.domain.com --deploy-hook f5deploy`

For Docker you would use:
```
docker run --rm  -it  \
-v "$(pwd)/out":/acme.sh  \
acme_f5 --deploy -d xyz.domain.com \ 
--deploy-hook f5deploy
```
**NOTE: When doing `--deploy` with a `--deploy-hook` the hook is stored permanently in the xyz.domain.com.conf file. 
If you also set a `--renew-hook` during `--issue`, it will store both and run both on-renewal, which shouldn't cause problems but is not ideal.**

## acme.sh daemon
If running as a daemon in docker and --restart is set to true (or any value that would allow a restart) you will need to use `-v "/full/path/to/out:/acme.sh"`. When the container restarts it does not maintain the original $(pwd). This is a docker peculiarity.

## Notes
On the F5 the following is created:
- Certificate & Key: xyz.domain.com
- Chain: xyz.domain.com.le-chain - this includes both the domain certificate and LetsEncrypt Authority.
- Client SSL Profile: cssl.xyz.domain.com. This profile is never overwritten and can be customized as required.

## Credits
@f5central for the API script modified from https://github.com/f5devcentral/lets-encrypt-python
