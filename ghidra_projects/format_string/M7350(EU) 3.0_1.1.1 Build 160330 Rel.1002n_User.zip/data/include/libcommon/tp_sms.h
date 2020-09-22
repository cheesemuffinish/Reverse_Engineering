/*******************************************************************************
  Copyright (C), 2014, TP-LINK TECHNOLOGIES CO., LTD.
  File name     : tp_sms.h
  Description   : define macro of sms module for common use
  Author        : liuchang<liuchang@tp-link.net>

  History:
------------------------------
V0.1, 2014-05-26, liuchang        create file.
*******************************************************************************/
#ifndef TP_SMS_H
#define TP_SMS_H

// SMS center number state related uci option
#define SMS_UCI_REPT_ENABLE   "sms.smsc_setting.rept_enable"
#define SMS_UCI_CTR_NUM       "sms.smsc_setting.smsc_number"
#define SMS_UCI_CTR_ENABLE    "sms.smsc_setting.smsc_enable"
#define SMS_UCI_SAVE_SENT_MSG_ENABLE "sms.smsc_setting.save_sent_msg_enable"

// Common define value of sms settings
#define DISABLE_STR "0"
#define ENABLE_STR  "1"

// UCI settings for SMS unread count and send result
#define SMS_UCI_UNREAD "sms.sms_state.unread_count"
#define SMS_UCI_SENDRESULT "sms.sms_send_result.sms_result"
#define SMS_UCI_SENDCAUSE "sms.sms_send_result.sms_cause"

#endif
