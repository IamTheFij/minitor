#! /bin/bash

HOST_ARCH=x86_64
VERSION=v2.9.1-1

mkdir -p build
cd build

# Multiple args can be passed in, but in most cases (Makefile and .drone.yml) we only use one at a time
for target_arch in $*; do
  wget https://github.com/multiarch/qemu-user-static/releases/download/$VERSION/${HOST_ARCH}_qemu-${target_arch}-static.tar.gz
  tar -xvf ${HOST_ARCH}_qemu-${target_arch}-static.tar.gz
  rm ${HOST_ARCH}_qemu-${target_arch}-static.tar.gz
done
