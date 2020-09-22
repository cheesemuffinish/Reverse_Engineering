#!/bin/sh

BCM_AP_SET="bcmApSet.sh"

WL="wlarm"

# MAC Address
RANDOM_MAC_ADDRESS="00:11:22:33:44:55"
UCI_MAC_ADDRESS="`uci get product.wlan.mac_address`"

# Network interfaces
BRIDGE_NAME="br0"
WLAN_NAME="eth0"

wlan_apset()
{
case "$1" in
start)
	# Check existence
	if [ ! -n "UCI_MAC_ADDRESS" ]; then
	    MAC_ADDRESS=$RANDOM_MAC_ADDRESS
	else
	    # Mac address in uci is like: 00-11-22-33-44-55
	    # But wlan driver need this: 00:11:22:33:44:55
	    # So convert '-' to ':' in MAC address
	    MAC_ADDRESS="`echo $UCI_MAC_ADDRESS | sed s/-/:/g`"
	fi

	# Pre wlan config: Enable network
	date_now=`date`
	echo "ifconfig ${WLAN_NAME} up, before date: ${date_now}"
	echo "WLAN: ifconfig ${WLAN_NAME} up, before date: ${date_now}" >> /dev/kmsg
	ifconfig ${WLAN_NAME} up

	date_now=`date`
	echo "ifconfig ${WLAN_NAME} up, after date: ${date_now}"
	echo "WLAN: ifconfig ${WLAN_NAME} up, after date: ${date_now}" >> /dev/kmsg

	# Check if dhd initialized successfully
	${WL} ver
	if [ $? -ne 0 ]; then
		echo "ifconfig up error..."
		echo "WLAN: ifconfig up error..." >> /dev/kmsg
		exit 1
	fi

	# Config wlan
	echo "${BCM_AP_SET} ${WL} ${MAC_ADDRESS}"
	echo "WLAN: ${BCM_AP_SET} ${WL} ${MAC_ADDRESS}" >> /dev/kmsg
	${BCM_AP_SET} ${WL} ${MAC_ADDRESS}

	# Post wlan config: bridge ops
	echo "brctl addif ${BRIDGE_NAME} ${WLAN_NAME}"
	echo "WLAN: brctl addif ${BRIDGE_NAME} ${WLAN_NAME}" >> /dev/kmsg
	brctl addif ${BRIDGE_NAME} ${WLAN_NAME}

	# Set promiscuous mode ethernet address reception
	${WL} promisc 0
;;
start_ftm)
	echo "ifconfig ${WLAN_NAME} up"
	echo "WLAN: ifconfig ${WLAN_NAME} up" >> /dev/kmsg
	ifconfig ${WLAN_NAME} up
;;
stop)
	echo "brctl delif ${BRIDGE_NAME} ${WLAN_NAME}"
	echo "WLAN: brctl delif ${BRIDGE_NAME} ${WLAN_NAME}" >> /dev/kmsg
	brctl delif ${BRIDGE_NAME} ${WLAN_NAME}
	${WL} down

	echo "ifconfig ${WLAN_NAME} down"
	echo "WLAN: ifconfig ${WLAN_NAME} down" >> /dev/kmsg
	ifconfig ${WLAN_NAME} down
;;
*)
	echo "Usage: $0 start | stop | start_ftm"
;;
esac
}

wlan_apset $@
