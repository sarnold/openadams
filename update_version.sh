#!/bin/sh

GIT_VERSION=$(git describe)
GIT_REV=$(git rev-parse --short HEAD)
GIT_COMMIT_DATE=$(git show  -s --format=%ci | sed "s:-:/:g; s/ +.*//")
BUILD_DATE=$(date +"%Y/%m/%d %H:%M:%S")

if git describe --dirty | grep -q "dirty$" ; then
  LOCAL_MODS=tainted
else
  LOCAL_MODS=untainted
fi


sed "s|%GIT_VERSION%|$GIT_VERSION|;
     s|%GIT_REV%|$GIT_REV|;
     s|%GIT_COMMIT_DATE%|$GIT_COMMIT_DATE|;
     s|%BUILD_DATE%|$BUILD_DATE|;
     s|%LOCAL_MODS%|$LOCAL_MODS|;" _naf_version.tmpl > _naf_version.py
