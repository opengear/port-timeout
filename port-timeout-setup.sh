#!/bin/bash

echo Copying files...
mv /home/root/port-timeout.py /etc/scripts/port-timeout
mv /home/root/port-timeout.service /etc/systemd/system/

echo
echo Setting up service...
systemctl daemon-reload
systemctl enable port-timeout.service

echo
echo Starting port-timeout.service...
systemctl start port-timeout.service
systemctl status port-timeout.service

echo
echo
echo Use systemctl to start/stop port-timeout.service
echo Example: systemctl start port-timeout.service
echo Example: systemctl stop port-timeout.service
echo