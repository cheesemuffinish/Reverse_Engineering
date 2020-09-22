#!/bin/sh

BRCM_DEVID="0a5c:bd1c"

ENUMDEV="bcmenumdev.sh"
ENUM_RETRY_LIMIT=5

BCMDL="bcmdl"

BCM_FW_PATH="/usr/bin/firmware/bcm/bcm43241"
FW="${BCM_FW_PATH}/fw.bin.trx"
TESTMODE_FW="${BCM_FW_PATH}/mfg.bin.trx"

BCM_DRV_NAME="dhd"
BCM_DRV_FILE_PATH="/lib/modules/3.4.0+/bcm"

# power level
DEFAULT_POWER_LEVEL="mid"
UCI_POWER_LEVEL="`uci get wlan.basic_setting.power_level`"

wlan_driver()
{
	if [ ! -n "UCI_POWER_LEVEL" ]; then
	    POWER_LEVEL=${DEFAULT_POWER_LEVEL}
	else
	    case ${UCI_POWER_LEVEL} in
		0)
			POWER_LEVEL="high"
			;;
		1)
			POWER_LEVEL="mid"
			;;
		2)
			POWER_LEVEL="low"
			;;
		*)
			POWER_LEVEL=${DEFAULT_POWER_LEVEL}
			;;
		esac
	fi

	NVRAM="${BCM_FW_PATH}/nvram_${POWER_LEVEL}.txt"

case "$1" in
start)
	lsmod |grep -q dhd
	ret1=$?

	lsusb |grep -q ${BRCM_DEVID}
	ret2=$?

	if [ ${ret1} -eq 0 ] || [ ${ret2} -eq 0 ]; then
		echo "WLAN: Before start, try to clean up first"
		echo "WLAN: Before start, try to clean up first" >> /dev/kmsg
		wlan_driver stop
		sleep 1
	fi

	echo "${ENUMDEV} start"
	echo "WLAN: ${ENUMDEV} start" >> /dev/kmsg
	${ENUMDEV} start
	sleep 1

	retry=0
	lsusb | grep -q $BRCM_DEVID
	while [ $? -ne 0 -a $retry -le $ENUM_RETRY_LIMIT ]; do
		echo "Enumeration failure, try again!"
		echo "WLAN: Enumeration failure, try again!" >> /dev/kmsg
		${ENUMDEV} restart
		retry=`expr $retry + 1`
		lsusb | grep -q $BRCM_DEVID
	done

	if [ $retry -gt $ENUM_RETRY_LIMIT ]; then
		echo "Enumeration Failed"
		echo "WLAN: Enumeration Failed" >> /dev/kmsg

		#just a workaround
		#reboot to make hsic host ok for wlan enumeration
		reboot
		exit 1
	fi

	echo "${BCMDL} -n ${NVRAM} ${FW}"
	echo "WLAN: ${BCMDL} -n ${NVRAM} ${FW}" >> /dev/kmsg
	${BCMDL} -n ${NVRAM} ${FW}
	usleep 200000

	echo "${BCM_DRV_FILE_PATH}/${BCM_DRV_NAME}.ko"
	echo "WLAN: ${BCM_DRV_FILE_PATH}/${BCM_DRV_NAME}.ko" >> /dev/kmsg
	insmod ${BCM_DRV_FILE_PATH}/${BCM_DRV_NAME}.ko
	usleep 200000

	echo "Starting CXMAPP..."
	echo "WLAN: Starting CXMAPP..." >> /dev/kmsg
	cxmapp --init
	cxmapp &

;;

start_ftm)
	echo "Factory mode starting..."
	echo "WLAN: Factory mode starting..." >> /dev/kmsg

	echo "${ENUMDEV} start"
	echo "WLAN: ${ENUMDEV} start" >> /dev/kmsg
	${ENUMDEV} start
	sleep 1

	echo "${BCMDL} -n ${NVRAM} ${TESTMODE_FW}"
	echo "WLAN: ${BCMDL} -n ${NVRAM} ${TESTMODE_FW}" >> /dev/kmsg
	${BCMDL} -n ${NVRAM} ${TESTMODE_FW}
	usleep 200000

	echo "${BCM_DRV_FILE_PATH}/${BCM_DRV_NAME}.ko"
	echo "WLAN: ${BCM_DRV_FILE_PATH}/${BCM_DRV_NAME}.ko" >> /dev/kmsg
	insmod ${BCM_DRV_FILE_PATH}/${BCM_DRV_NAME}.ko
	usleep 200000

;;

stop)
	date_now=`date`
	echo "rmmod ${BCM_DRV_NAME}, before date: ${date_now}"
	echo "WLAN: rmmod ${BCM_DRV_NAME} before date: ${date_now}" >> /dev/kmsg
	rmmod ${BCM_DRV_NAME}
	date_now=`date`
	echo "rmmod ${BCM_DRV_NAME} after date: ${date_now}"
	echo "WLAN: rmmod ${BCM_DRV_NAME} after date: ${date_now}" >> /dev/kmsg

	echo "${ENUMDEV} stop"
	echo "WLAN: ${ENUMDEV} stop" >> /dev/kmsg
	${ENUMDEV} stop

	echo "Stopping CXMAPP..."
	echo "WLAN: Stopping CXMAPP..." >> /dev/kmsg
	killall -15 cxmapp

;;

*)
	echo "Usage: $0 start | stop | start_ftm"
;;
esac
}

wlan_driver $@
