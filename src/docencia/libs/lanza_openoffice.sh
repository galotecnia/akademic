#!/bin/sh

HOST=$(hostname)
PORT=2002
XSERVER=/usr/bin/Xvfb
DISPLAY=:99
SOFFICE=/usr/lib/openoffice/program/soffice.bin
ARGS="-display $DISPLAY -nologo -nodefault -accept=socket,host=$HOST,port=$PORT;urp;StarOffice.ComponentContext"

case $1 in
	start)
		start-stop-daemon --start --background --exec $XSERVER -- $DISPLAY
		start-stop-daemon --start --background --exec $SOFFICE -- $ARGS
		;;
	stop)
		start-stop-daemon --stop --exec $SOFFICE
		start-stop-daemon --stop --exec $XSERVER
		;;
esac

