#!/bin/bash -ex
#
# Find available versions of Tor Browser Android and download/verify
# any newer releases that are not present in this repo.  This script
# is meant to run frequently in a cron job, perhaps as much as every 5
# minutes.  It forces connections over Tor to prevent targetting this
# process.

download_and_verify() {
    set -e
    version=$1
    apk=$2
    if ! wget --quiet --continue https://dist.torproject.org/torbrowser/${version}/${apk}.asc; then
	printf "\nERROR ${apk}.asc\n\n"
	return
    fi

    wget --quiet --continue https://dist.torproject.org/torbrowser/${version}/${apk}
    if gpg --verify ${apk}.asc; then
	packageName=`androguard apkid $apk | jq --raw-output .[][0]`
	versionCode=`androguard apkid $apk | jq --raw-output .[][1]`
	if [ $packageName == "org.torproject.torbrowser" ]; then
	    ln ${apk} ../repo/${packageName}_${versionCode}.apk
	    ln ${apk}.asc ../repo/${packageName}_${versionCode}.apk.asc
	fi
    fi
}

http_proxy=http://localhost:54321
https_proxy=http://localhost:8081
SOCKS_SERVER=locahost:9050

if [ "`curl --silent https://check.torproject.org/api/ip | jq .IsTor`" != "true" ]; then
    echo ERROR not running over tor!
    #exit 1  TODO REMOVE ME
fi

cd $(dirname $0)/tmp
for version in `curl --silent https://dist.torproject.org/torbrowser/ | sed -En 's,.*>([0-9]+\.[0-9.]+)/?<.*,\1,p' | sort --reverse`
do
    arch=aarch64
    apk=tor-browser-${version}-android-${arch}-multi.apk
    if [ -e $apk ]; then
	echo Skipping existing tmp/$apk
    else
	download_and_verify $version $apk &
    fi
done
wait
