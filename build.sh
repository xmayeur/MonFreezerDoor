#!/bin/sh

git pull
docker rm -f monfreezer
docker build -t monfreezer . && \
docker tag monfreezer xmayeur/monfreezer

chmod +x monfreezer.sh
sudo cp MonFreezeDoor.conf monfreeze.sh /root
/bin/sh ./monfreezer.sh

#docker push xmayeur/monfreezer && \

