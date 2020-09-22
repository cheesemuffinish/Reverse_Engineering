/*******************************************************************************
  Copyright (C), 1996-2014, TP-LINK TECHNOLOGIES CO., LTD.
  File name     : ubus_event.h
  Description   : define ubus event for common use
  Author        :

  History:
------------------------------
V0.1, 2014-04-30, zhangtao create file.
*******************************************************************************/

#ifndef _UBUS_EVENT_H_
#define _UBUS_EVENT_H_

/************************** Define ubus event of USB **************************/

#define USB_EVENT_TYPE		"usb_event_type"

/* The state of USB, refer to usb_online_state_t */
#define USB_ONLINE_STATE	"usb_online_state"

typedef enum {
	USB_DISCONNECT = 0,
	USB_CONNECT,
} usb_online_state_t;


/****************** Define ubus event of WLAN Manager STARTS ****************/

/* WLAN event has three categories:
	- WLAN switch on/off
	- STA change
	- WPS
 */
#define WLAN_EVENT_TYPE		"wlan_event"

/*  When WLAN switches on/off, this one is issued with parameter
    "on" or "off" like below:
	{ "wlan_event": {"wlan_switch":"on"} }
	{ "wlan_event": {"wlan_switch":"off"} }
	{ "wlan_event": {"wlan_switch":"booting"} }
 */
#define WLAN_EVENT_SWITCH	"wlan_switch"
#define WLAN_EVENT_SWITCH_ON		"on"
#define WLAN_EVENT_SWITCH_OFF		"off"
#define WLAN_EVENT_SWITCH_BOOTING	"booting"
#define WLAN_EVENT_SWITCH_RESTARTING "restarting"

/*  When any STA changes, this one is issued with parameter of
    current sta number like below:
	{ "wlan_event": {"current_sta_num":"1"} }
 */
#define WLAN_EVENT_STA_CHANGE	"current_sta_num"

/*  WPS related events are issued with parameter of one of the
    following:
	- wps_start
	- wps_success
	- wps_failure
	- wps_pbc_overlap
	- wps_timeout

    Example:
	{ "wlan_event": {"wps_event":"wps_start"} }
	{ "wlan_event": {"wps_event":"wps_success"} }
 */
#define WLAN_EVENT_WPS		"wps_event"
 #define WLAN_EVENT_WPS_START		"wps_start"
 #define WLAN_EVENT_WPS_SUCCESS		"wps_success"
 #define WLAN_EVENT_WPS_FAILURE		"wps_failure"
 #define WLAN_EVENT_WPS_TIMEOUT		"wps_timeout"
 #define WLAN_EVENT_WPS_PBC_OVERLAP	"wps_pbc_overlap"

/******************* Define ubus event of WLAN Manager ENDS *****************/




/****************** Define ubus event of webserver ****************/

#define WEBSERVER_EVENT_TYPE "webserver_event_type"

// language value is read from the web, and it will be saved in to webserver.user_config.language
#define WEBSERVER_NEW_LANGUAGE "webserver_new_language"


/******************* Define ubus event of webserver ENDS *****************/



/************************ ubus event for system_state *************************/
/* ubus event:
shutdown:
{ "system_state": {"state_event":"shutdown normal"} }
{ "system_state": {"state_event":"shutdown low_power"} }
{ "system_state": {"state_event":"shutdown too_hot"} }
{ "system_state": {"state_event":"shutdown too_cold"} }
reboot:
{ "system_state": {"state_event":"reboot normal"} }
{ "system_state": {"state_event":"reboot recovery"} }
power_bank:
{ "system_state": {"state_event":"power_bank on"} }
{ "system_state": {"state_event":"power_bank off"} }
off_chg:
{ "system_state": {"state_event":"off_chg on"} }
{ "system_state": {"state_event":"off_chg off"} }
factory_reset:
{ "system_state": {"state_event":"factory_reset"} }
shutdown 3G/4G:
{ "system_state": {"state_event":"shutdown 4g"} }
shutdown WiFi:
{ "system_state": {"state_event":"shutdown wifi"} }
 */

#define SYSTEM_STATE_TYPE "system_state"
#define SYSTEM_STATE_EVENT "state_event"

#define SYSTEM_STATE_SHUTDOWN_NORMAL "shutdown normal"
#define SYSTEM_STATE_SHUTDOWN_LOW_POWER "shutdown low_power"
#define SYSTEM_STATE_SHUTDOWN_TOO_HOT "shutdown too_hot"
#define SYSTEM_STATE_SHUTDOWN_TOO_COLD "shutdown too_cold"

#define SYSTEM_STATE_REBOOT_NORMAL "reboot normal"
#define SYSTEM_STATE_REBOOT_RECOVERY "reboot recovery"

#define SYSTEM_STATE_POWER_BANK_ON "power_bank on"
#define SYSTEM_STATE_POWER_BANK_OFF "power_bank off"

#define SYSTEM_STATE_OFF_CHG_ON "off_chg on"
#define SYSTEM_STATE_OFF_CHG_OFF "off_chg off"

#define SYSTEM_STATE_FACTORY_RESET "factory_reset"

/* [wangdongyang start] Add shutdown/bringup 4G and shutdownWiFi ubus event */
#define SYSTEM_STATE_SHUTDOWN_4G "shutdown 4g"
#define SYSTEM_STATE_BRINGUP_4G "bringup 4g"
#define SYSTEM_STATE_SHUTDOWN_WIFI "shutdown wifi"
/* [wangdongyang end] */

// [zhouqingkui start]
// Add ubus event for connecting/disconnecting backhaul
#define MOBILE_DATA_OPERATION_TYPE "mobile_operation"
#define MOBILE_DATA_OPERATION_EVENT "mobile_event"
#define MOBILE_DATA_OPERATION_BRINGUP "bringup"
#define MOBILE_DATA_OPERATION_TEARDOWN "teardown"

// Add ubus event for turning roam switch on/off
#define ROAM_OPERATION_TYPE "roam_operation"
#define ROAM_OPERATION_EVENT "roam_event"
#define ROAM_OPERATION_TURNON "turnon"
#define ROAM_OPERATION_TURNOFF "turnoff"
// [zhouqingkui end]

/******************************************************************************/

// [wangdongyang start] Add ubus event for SIM.
/************************ ubus event for SIM *************************/
/* ubus event:
SIM state changed:
{ "sim_state": {"state_event":"changed"} }
*/
#define SIM_STATE_EVENT_TYPE "sim_state"
#define SIM_STATE_EVENT_KEY "state_event"
#define SIM_STATE_EVENT_VALUE_CHANGED "changed"
/*********************************************************************/
// [wangdongyang end]

//[yaohuachao start]
#define RNDIS_INFO_TYPE		"rndis_info"
#define RNDIS_INFO_EVENT	"get_rndis_info"
//[yaohuachao end]

#endif /* _UBUS_EVENT_H_ */


