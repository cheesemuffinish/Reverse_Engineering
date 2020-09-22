/*******************************************************************************
  Copyright (C), 2014, TP-LINK TECHNOLOGIES CO., LTD.
  File name   : charger.h
  Description : Header file of control module of charge ic mp2617.
  Author      : linyunfeng

  History:
------------------------------
V0.3, 2014-06-18, linyunfeng    move common type define to libcommon.
V0.2, 2014-05-05, linyunfeng    complete the control module of mp2617.
V0.1, 2014-04-14, linyunfeng    create file.
*******************************************************************************/
#ifndef __CHARGE_H__
#define __CHARGE_H__

typedef enum {
	STATE_OFF = 0,
	STATE_ON,
} state_status_t;

/* Battery health state */
typedef enum {
	POWER_SUPPLY_HEALTH_UNKNOWN = 0,	/* Unknown */
	POWER_SUPPLY_HEALTH_GOOD,		/* 45 > T >= 0 */
	POWER_SUPPLY_HEALTH_OVERHEAT,		/* 60 > T >= 45 */
	POWER_SUPPLY_HEALTH_DEAD,		/* T >= 60 */
	POWER_SUPPLY_HEALTH_OVERVOLTAGE,
	POWER_SUPPLY_HEALTH_UNSPEC_FAILURE,	/* No battery */
	POWER_SUPPLY_HEALTH_COLD,		/* 0 > T >= -20 */
	POWER_SUPPLY_HEALTH_DEAD_OVERCOLD,	/* -20 > T >= -50 */
} batt_health_status;

/* UCI define */
#define UCI_POWER_LEVEL		"battery.battery_mgr.power_level"
#define UCI_HEALTH_STATE	"battery.battery_mgr.health_state"
#define UCI_CHARGING		"battery.battery_mgr.is_charging"

#endif	/* __CHARGE_H__ */

