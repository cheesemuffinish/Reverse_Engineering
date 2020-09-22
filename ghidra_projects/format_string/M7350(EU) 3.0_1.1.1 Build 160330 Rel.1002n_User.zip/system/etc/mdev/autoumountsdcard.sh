#! /bin/sh
MASS_STORAGE_FILE=/sys/devices/virtual/android_usb/android0/f_mass_storage/lun/file

umount_sdcard_link()
{
  SDCARDS_TO_UMOUNT=`mount | grep "sdcard" | cut -d ' ' -f 3`
  if test -z "${SDCARDS_TO_UMOUNT}"
  then
    exit 0
  fi
  SDCARD_TO_UMOUNT=
  for SDCARD_TO_UMOUNT in ${SDCARDS_TO_UMOUNT}
  do
    umount ${SDCARD_TO_UMOUNT}
  done
}

stop_samba
stop_vsftpd
umount /media/card 2>/dev/null
echo "" > ${MASS_STORAGE_FILE}
umount_sdcard_link

