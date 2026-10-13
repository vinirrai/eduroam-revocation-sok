#!/bin/bash
# Run testbed experiments inside the Ubuntu 24.04 container (works on macOS and Linux).
# The repo is mounted at /sok, so output lands in testbed/results/ on the host.
#
# usage: ./run_all.sh build              build the image (done automatically if missing)
#        ./run_all.sh selftest           each mechanism: login before and after graduation
#        ./run_all.sh latency [N]        median login time per mechanism (default N=40)
#        ./run_all.sh window [T]         time from graduation to first reject (default T=330 s)
#        ./run_all.sh server             server direction: OCSP stapling vs eapol_test ocsp=0/1/2
#        ./run_all.sh privacy            is the device cert name visible to relays (TLS 1.2 vs 1.3)
#        ./run_all.sh all                selftest, server and privacy (the quick ones)
#        ./run_all.sh shell              interactive shell in the container
set -e
REPO=$(cd "$(dirname "$0")" && pwd)
IMG=eduroam-tb

build() { docker build -t $IMG "$REPO"; }
docker image inspect $IMG >/dev/null 2>&1 || build

run() { # run a command in a fresh container with the student-direction services up
  local tty=""; [ -t 1 ] && tty="-t"
  docker run --rm -i $tty -v "$REPO":/sok -e ONLY $IMG bash -c "mkdir -p results && $1"
}
START="./pki.sh init && ./ldap.sh start"

case ${1:-all} in
build)    build ;;
selftest) run "$START && python3 harness.py selftest" ;;
latency)  run "$START && python3 harness.py latency ${2:-40}" ;;
window)   run "$START && python3 harness.py window ${2:-330}" ;;
server)   run "python3 server_exp.py" ;;
privacy)  run "python3 server_exp.py >/dev/null && python3 privacy_exp.py" ;;
all)      run "$START && python3 harness.py selftest && python3 server_exp.py && python3 privacy_exp.py" ;;
shell)    docker run --rm -it -v "$REPO":/sok $IMG bash ;;
*)        sed -n 2,12p "$0"; exit 1 ;;
esac
