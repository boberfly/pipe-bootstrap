# We start with CentOS 7, because it is commonly used in
# production, and meets the glibc requirements of VFXPlatform 2018
# (2.17 or lower).

FROM centos:7

RUN yum install -y centos-release-scl && \
    yum install -y devtoolset-6 && \
    yum install -y epel-release && \
    yum install -y cmake3 && \
    yum install -y patch && \
    yum install -y wget && \
    yum install -y curl && \
    ln -s /usr/bin/cmake3 /usr/bin/cmake

# Copy over build script and set an entry point that
# will use the compiler we want.

COPY dependencies ./dependencies
COPY build.py ./

ENTRYPOINT [ "scl", "enable", "devtoolset-6", "--", "bash" ]