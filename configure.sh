#!/usr/bin/env sh

# restore original f5deploy.sh and create new backup
if [ -f "f5deploy.sh.1" ]; then
  rm f5deploy.sh && cp f5deploy.sh.1 f5deploy.sh
else
  cp f5deploy.sh f5deploy.sh.1
fi

chmod +x ./f5deploy/f5deploy.py

while [ ${#} -gt 0 ]; do
      case "${1}" in
        --nodocker)
          _no_dockerbuild=1
          ;;
        --deploy-path)
          echo "path?"
          _deploy_path="$2"
          shift
          ;;
      esac
      shift 1
done

_script_path=$(pwd)/f5deploy/f5deploy.py

echo "Setting python script directory to $_script_path in f5deploy.sh"

sed -i 's|^.*--nodocker.*$|    '"$_script_path"' \$\*|g' f5deploy.sh

if ! [ -z ${_deploy_path+x} ]; then
  echo "Copying f5deploy.sh to $_deploy_path"
  cp f5deploy.sh $_deploy_path
fi

if [ -z ${_no_dockerbuild+x} ]; then
  echo "Building docker image for acme_f5 from local directory."
  docker build -t acme_f5 .
  if [ $? -eq 0 ]; then
    exit 1
  fi
else
  echo "Skipping Docker build."
fi
