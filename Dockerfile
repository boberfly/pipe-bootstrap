# We start with CentOS 7, because it is commonly used in
# production, and meets the glibc requirements of VFXPlatform 2018
# (2.17 or lower).

FROM centos:7

RUN yum install -y centos-release-scl && \
    yum install -y devtoolset-6 && \
    yum install -y epel-release
RUN yum install -y patch && \
    yum install -y wget && \
    yum install -y curl && \
    yum install -y nano && \
    yum install -y zip && \
    yum install -y git

# Copy over build script and set an entry point that
# will use the compiler we want.

COPY dependencies ./dependencies
COPY scripts ./
COPY build.py ./

ENTRYPOINT [ "scl", "enable", "devtoolset-6", "--", "bash" ]