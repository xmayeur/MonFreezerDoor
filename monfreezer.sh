#!/bin/sh

# wget  https://raw.githubusercontent.com/xmayeur/spammon/master/SpamMon.conf

docker rm -f monfreezer
docker run -ti --name monfreezer -v /root/:/conf/ -v /var/log:/var/log/ monfreezer

