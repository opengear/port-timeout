# port-timeout
Timeout Active User Sessions from Serial Console Ports

Stand Alone Script Usage:
- Use -t to specify timeout timer in seconds
- Use -w to specify the wait timer in seconds
   - Example: python3 portTimeout.py -t 60 -w 60
     
If no value -t or -w is given, the default value of 30s is used for both

Run script as a service:
1. Edit port-timeout.service line 7 with custom timers if desired (defaults are 30s)
   Example: ExecStart=/usr/bin/python3 /etc/scripts/port-timeout -t 60 -w 60
2. Copy files to your Operations Manager to directory /home/root
3. Run port-timeout-setup.sh

   Check the status, start, or stop of the service with systemctl.
   
   - systemctl start port-timeout
   - systemctl stop port-timeout
   - systemctl status port-timeout
   

Script events log to /var/log/messages.
