#! /bin/sh

if [ "$1" == "" ]; then
    exit 1
fi

mmcblk=`ls /dev | grep $1 | wc -l`
mounted=`mount | grep $1 | wc -l`

if [ $mmcblk -ge 1 ]; then
    if [ $mounted -le 0 ]; then
        mount /dev/$1 /media/card
    fi
fi

if [ $mmcblk -le 0 ]; then
    if [ $mounted -ge 0 ]; then
        umount /media/card
    fi
fi

