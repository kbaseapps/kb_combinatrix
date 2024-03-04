#!/bin/sh

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties
  sh ./scripts/start_server.sh
elif [ "${1}" = "async" ] ; then
  python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties
  sh ./scripts/run_async.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  sh ./test/run_tests.sh
elif [ "${1}" = "bash" ] ; then
  echo "The alpine image does not use a bash shell."
  sh
elif [ "${1}" = "sh" ] ; then
  sh
elif [ "${1}" = "report" ] ; then
  cp ./compile_report.json work/compile_report.json
  echo ./work/compile_report.json
else
  echo Unknown command: ${1}
fi
