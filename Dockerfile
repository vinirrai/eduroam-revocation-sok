# Ubuntu 24.04 image for the testbed. The repo is mounted at /sok at run time,
# so editing scripts on the host does not need a rebuild. See run_all.sh.
FROM ubuntu:24.04
COPY testbed/setup.sh /tmp/setup.sh
RUN bash /tmp/setup.sh && rm -rf /var/lib/apt/lists/* /tmp/setup.sh
WORKDIR /sok/testbed
