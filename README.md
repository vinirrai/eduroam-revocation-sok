# eduroam revocation SoK

SoK and testbed on credential revocation in federated Wi-Fi (eduroam-style 802.1X/EAP), for COMP 790-194 at UNC.

Everything runs on localhost. Nothing here touches a real network.

Quick start (Ubuntu 24.04, as root):

    cd testbed
    ./setup.sh
    ./pki.sh init
    ./ldap.sh start
    python3 harness.py selftest

See docs/PLAN.md for the full plan and what each script does.
