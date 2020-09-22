#!/bin/sh

#args are as follows: action mac ip hostname

if [ "$1" = "add" -o "$1" = "old" ]
then
    uci set dhcp_var.hostname_item.${2//:/_}=$4
    uci commit dhcp_var
fi