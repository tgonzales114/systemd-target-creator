#!/bin/bash

function usage () {
    echo "usage: $0 CUSTOM_TARGET_NAME FROM_RPM_REPO"
    echo "example: $0 hashi hashicorp"
}

function print_output () {
    echo "created custom target: ${TARGET}.target"
    echo "created files:"
    printf "  - %s\n" "$TARGET_FILE" "${SERVICE_OVERRIDES[@]}"
    echo "control commands:"
    echo "  # check for status of target dependencies (a bit verbose)"
    echo "  systemctl list-dependencies hashi.target"
    echo
    echo "  # stop all services controlled by target"
    echo "  systemctl stop hashi.target"
    echo
    echo "  # start all services controlled by target"
    echo "  systemctl start hashi.target"

}

function create_target () {
    TYPE="[Unit]"
    DESC="Description=Custom Target $TARGET of Services From Repo $FROM_REPO"
    REQUIRE="Requires=multi-user.target network.target"
    AFTER="After=multi-user.target network.target"
    CONFLICT="Conflicts=emergency.target rescue.target"
    ISOLATE="AllowIsolate=no"

    DIR="/etc/systemd/system"
    FILE="${TARGET}.target"
    FILE_PATH="${DIR}/${FILE}"

    export TARGET_FILE=$FILE_PATH
    printf "%s\n" "$TYPE" "$DESC" "$REQUIRE" "$AFTER" "$CONFLICT" "$ISOLATE" > $FILE_PATH
}

function find_services () {
    INPUT_FILE="output.txt"
    if [[ ! -f $INPUT_FILE ]]; then
        echo "could not find input file: $INPUT_FILE"; exit 1
    fi
    export SERVICES=$(grep "$FROM_REPO" $INPUT_FILE | awk -F' - ' '{print $1}' | awk -F': ' '{print $2}')
}

function modify_service () {
    UNIT="[Unit]"
    STOP="StopWhenUnneeded=yes"
    INST="[Install]"
    WANT="WantedBy=${TARGET}.target"

    DIR="${SERVICE_FILE}.d"
    FILE="override.conf"
    FILE_PATH="${DIR}/$FILE"

    mkdir -p $DIR

    export SERVICE_OVERRIDES+=("$FILE_PATH")
    printf "%s\n" "$UNIT" "$STOP" "" "$INST" "$WANT" > $FILE_PATH
    SERVICE=$(basename $SERVICE_FILE)
    TARGET_WANTS="Wants=$SERVICE"
    echo $TARGET_WANTS >> /etc/systemd/system/${TARGET}.target
}

function main () {
    if [[ "$#" < "2" ]]; then
        usage; exit 1
    fi
    export TARGET=$1
    export FROM_REPO=$2
    create_target
    find_services
    SERVICE_OVERRIDES=()
    for SERVICE_FILE in $SERVICES; do
        export SERVICE_FILE=$SERVICE_FILE
        modify_service
    done
    print_output
}
main $@
