#!/bin/sh
# Reenum Bcm 43241 chip, whose power is supplied via

# GPIO Settings
# MDM9225	BCM43241	Description
#-----------------------------------------------
# GPIO 65	REG_ON		BCM power switch
# GPIO 63	PM		BCM low power control
#
# For more information, please refer to datasheet.
#
GPIO_REG_ON=65
GPIO_PM=63

COMMAND_NAME="reenumdev.sh"

bcm_enum_chip() {
	case "$1" in
	start)
		echo "Start enum bcm chip 43241..."

		# Export GPIOs
		echo "${GPIO_REG_ON}" > /sys/class/gpio/export
		echo "${GPIO_PM}" > /sys/class/gpio/export
		## Pull down REG_ON
		echo "out" > /sys/class/gpio/gpio${GPIO_REG_ON}/direction
		echo "0" > /sys/class/gpio/gpio${GPIO_REG_ON}/value
		## Pull up PM and stay when at work
		echo "out" > /sys/class/gpio/gpio${GPIO_PM}/direction
		echo "1" > /sys/class/gpio/gpio${GPIO_PM}/value

		# Unbind hsic
		echo msm_hsic_host > /sys/bus/platform/drivers/msm_hsic_host/unbind
		sleep 1

		# Pull up REG_ON to power up Bcm 43241
		echo "1" > /sys/class/gpio/gpio${GPIO_REG_ON}/value

		# Bind hsic
		echo msm_hsic_host > /sys/bus/platform/drivers/msm_hsic_host/bind

	;;
	stop)
		echo "Remove bcm chip 43241 from hsic"

		# Unbind hsic
		echo msm_hsic_host > /sys/bus/platform/drivers/msm_hsic_host/unbind

		# Power off Bcm 43241
		echo "0" > /sys/class/gpio/gpio${GPIO_REG_ON}/value
		echo "0" > /sys/class/gpio/gpio${GPIO_PM}/value

		# unexport GPIO
		echo "${GPIO_REG_ON}" > /sys/class/gpio/unexport
		echo "${GPIO_PM}" > /sys/class/gpio/unexport

	;;
	restart)
		bcm_enum_chip stop
		bcm_enum_chip start

		return $?

	;;
	*)
		echo "Usage: ${COMMAND_NAME} start|stop|restart"
		return 1

	;;
	esac
}

bcm_enum_chip $@
