#!/bin/bash

function find_service_files () {
    SRC1="/usr/lib/systemd/system"
    SRC2="/etc/systemd/system"
    export SERVICE_FILES=$(find $SRC1 $SRC2 -name '*.service' ! -type l)
}

function find_rpm () {
    if [[ -z "$FILE" ]]; then
        exit 1
    fi
    export RPM="none"
    if rpm -qf $FILE &> /dev/null; then
        export RPM=$(rpm -qf $FILE)
    fi
}

function find_service () {
    if [[ -z "$FILE" ]]; then
        exit 1
    fi
    export SERVICE=$(basename $FILE)
}

function find_repo () {
    if [[ -z "$RPM" ]]; then
        exit 1
    fi
    export REPO="none"
    if [[ "$RPM" != "none" ]]; then
        export REPO=$(yum info -C $RPM | grep 'From repo' | awk -F': ' '{print $2}')
    fi
}

function print_output () {
    echo "FILE: $FILE - SERVICE: $SERVICE - RPM: $RPM - REPO: $REPO"
}

function main () {
    find_service_files
    for FILE in $SERVICE_FILES; do
        export FILE=$FILE
	find_rpm
	find_service
	find_repo
	print_output
    done
}

main
