#!/bin/sh

git pull

docker rm -f monfreezer

docker build -t monfreezer . && \
docker tag monfreezer xmayeur/monfreezer && \
#docker push xmayeur/monfreezer

chmod +x monfreezer.sh build.sh
sudo cp MonFreezeDoor.conf monfreezer.sh /root

exec ./monfreezer.sh



