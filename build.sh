#!/bin/sh

git pull
docker rm -f monfreezer
docker build -t monfreezer . && \
docker tag monfreezer xmayeur/monfreezer && \
exec ./monfreezer.sh

#docker push xmayeur/monfreezer && \

