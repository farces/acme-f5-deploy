#!/usr/bin/env sh

# Sample script for f5deploy - hardcoded script location for use in Docker.

########  Public functions #####################

#domain keyfile certfile cafile fullchain
f5deploy_deploy() {
  _cdomain="$1"
  _ckey="$2"
  _ccert="$3"
  _cca="$4"
  _cfullchain="$5"

  _debug _cdomain "$_cdomain"
  _debug _ckey "$_ckey"
  _debug _ccert "$_ccert"
  _debug _cca "$_cca"
  _debug _cfullchain "$_cfullchain"

  # If using outside of docker, change this to the correct absolute path.
  /acme.sh/f5deploy/f5deploy.py $1
  if [ $? -eq 0 ]; then
    return 1
  fi
}