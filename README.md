# eduroam revocation SoK

SoK and testbed on credential revocation in federated Wi-Fi (eduroam-style 802.1X/EAP), for COMP 790-194 at UNC.

Everything runs on localhost. Nothing here touches a real network.

## Quick start (any machine with Docker, including macOS)

    ./run_all.sh selftest

This builds an Ubuntu 24.04 image on first use, mounts the repo at `/sok` and runs the experiment inside the container. Output goes to `testbed/results/`. Other commands: `latency [N]`, `window [T]`, `server`, `privacy`, `all`, `shell`. Run `./run_all.sh help` for the list.

## Quick start (Ubuntu 24.04, as root, no Docker)

    cd testbed
    ./setup.sh
    ./pki.sh init
    ./ldap.sh start
    python3 harness.py selftest

## Tool versions

Ubuntu 24.04 packages as of Oct 2026, measured in the Docker image on arm64 (Apple Silicon). The early results came from an x86_64 Ubuntu box with the same FreeRADIUS, wpa_supplicant and OpenSSL releases.

| Tool | Version |
|---|---|
| FreeRADIUS | 3.2.5 (3.2.5+dfsg-3~ubuntu24.04.3) |
| eapol_test (wpa_supplicant) | 2.10 (2:2.10-21ubuntu0.4) |
| hostapd | 2.10 (2:2.10-21ubuntu0.4) |
| OpenLDAP slapd | 2.6.10 |
| OpenSSL | 3.0.13 |
| Python | 3.12.3 |

Ubuntu may ship newer patch releases later. Each run should record the versions it used.

See docs/PLAN.md for the full plan and what each script does.
