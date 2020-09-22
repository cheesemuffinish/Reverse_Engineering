#!/bin/sh

# Driver load and devices enumerate
BCMWLANDRI="bcmwlan_ap0.sh"
# BCM WLAN setting
BCMAPSET="bcmwlan_ap1.sh"

wlan_ap()
{
case "$1" in
start)
	echo "${BCMWLANDRI} start"
	echo "WLAN: ${BCMWLANDRI} start" >> /dev/kmsg
	${BCMWLANDRI} start

	echo "${BCMAPSET} start"
	echo "WLAN: ${BCMAPSET} start" >> /dev/kmsg
	${BCMAPSET} start
;;
start_ftm)
	echo "${BCMWLANDRI} start_ftm"
	echo "WLAN: ${BCMWLANDRI} start_ftm" >> /dev/kmsg
	${BCMWLANDRI} start_ftm

	echo "${BCMAPSET} start_ftm"
	echo "WLAN: ${BCMAPSET} start_ftm" >> /dev/kmsg
	${BCMAPSET} start_ftm
;;
stop)
	echo "${BCMAPSET} stop"
	echo "WLAN: ${BCMAPSET} stop" >> /dev/kmsg
	${BCMAPSET} stop

	echo "${BCMWLANDRI} stop"
	echo "WLAN: ${BCMWLANDRI} stop" >> /dev/kmsg
	${BCMWLANDRI} stop
;;
*)
	echo "Usage: $0 start | stop | start_ftm"
;;
esac
}

wlan_ap $@
