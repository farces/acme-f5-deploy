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

  if grep docker /proc/1/cgroup -qa; then
    # we're in docker
    /acme.sh/f5deploy/f5deploy.py $*
    if ! [ $? -eq 0 ]; then
      return ?$
    fi
  else
    #we're running local
    echo "run build.sh --nodocker to set script path" && return 1
    if ! [ $? -eq 0 ]; then
      return $?
    fi
  fi
  return 0
}
