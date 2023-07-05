#!/usr/bin/python3
#
# port-timeout.py, v1.0
# Opengear Solution Engineering
# Jira: SLE-232, SLE-238, FR-1847
# Updated 29 June 2023 by M.Witmer
#
# Timeout serial console sessions on Cisco IOS devices
# Events are logged to /var/log/messages
# NOTE: Not tested on USB serial ports
#
# Usage:
# Use -t to specify timeout timer in seconds
# Use -w to specify the wait timer in seconds
# If no value -t or -w is given, the default value of 30s is used for both
# e.g. python3 portTimeout.py -t 60 -w 60

v = "1.0"
GNU = """
GNU GENERAL PUBLIC LICENSE, Version 3
This program is free software: you can redistribute it and/or modify     
it under the terms of the GNU General Public License as published by     
the Free Software Foundation, either version 3 of the License or any later version.

https://www.gnu.org/licenses/gpl-3.0.en.html

"""


import argparse
import json
import os
import requests
import subprocess
import syslog
import time
from os.path import expanduser
from ogshared.raml_api import overrides

TOKENFILE = expanduser("~/.token")

uri = "https://localhost/api/v2/"

# Get user defined timeout timer and wait timer (or use default)
parser = argparse.ArgumentParser()
parser.add_argument("-t", help="Console logout timer in seconds", type=int, default=30)
parser.add_argument("-w", help="Wait timer if no active sessions detected", type=int, default=30)
args = parser.parse_args()


# Create local API token
def createToken():

    # minimal, fast-loading requests alternative
    import ogshared.requests_lite as requests

    # use current cli session to fetch an api token
    cli_session_binary = getattr(overrides, "CLI_SESSION_BINARY", "/usr/libexec/cli-session")

    token = subprocess.run([cli_session_binary], stdout=subprocess.PIPE).stdout.decode("utf-8")

	# write token to file
    with open(TOKENFILE, "w") as f:
          f.write(token)

	# store token in var header
    headers = { "Authorization" : "Token " + token }

    return headers

# Look for active serial port user sessions and grab port
def checkSessions(headers):

    print("Checking for active console sessions...")
    syslog.syslog("Checking for active console sessions.")
     
    r = requests.get(f"{uri}ports", headers=headers, verify=False)

    s = r.json()

    n = 0

    # Iterate through ports with active sessions.
    # Current behavior stops and monitors the first active port, then moves onto the next when inactive.
    for x in s["ports"]:
        while True:
            if x["sessions"]:
                n = 1
                y = x["sessions"]
                portName = y[0]['port']
                portNum = portName.strip("ports-")
                if int(portNum) <= 9:
                    port = (f"0{portNum}")
                    sdata = (f"port{port}")
                else:
                    sdata = (f"port{portNum}")
                timeoutCheck(headers, sdata, portName)
                break
            else:
                break

    if n == 0:
        print(f"\nNo active console sessions. Waiting {args.w}s before checking again...\n")
        syslog.syslog(f"\nNo active console sessions. Waiting {args.w}s before checking again.")
        time.sleep(args.w)
        checkSessions(headers)
    else:
        pass
                
# API call to get TX counters based on active user session         
def checkCounters(headers, portName):

    r = requests.get(f"{uri}ports/ports_status/{portName}", headers=headers, verify=False)
    
    s = json.loads(r.text)

    txData = s["port_status"]["tx"]

    return txData

# Check and compare counters to determine if timeout critiria is met.
# If an active user transmits data during the timer period, then tx1<tx2 and function restarts.
# Criteria for timeout is met when tx1=tx (no user activity).
def timeoutCheck(headers, sdata, portName):

    # Initial check of TX counter
    tx1 = checkCounters(headers, portName)
    print(f"\nChecking TX counters for {sdata}...\n")
    syslog.syslog(f"\nChecking TX counters for {sdata}.")

    print(f"Waiting on timer ({args.t}s)...")
    syslog.syslog(f"Waiting on timer ({args.t}s).")

    # Visual timer is just for cool factor and visual debug while testing...
    time.sleep(args.t)
    
    print(f"Re-checking TX counters for {sdata}...\n")
    syslog.syslog(f"Re-checking TX counters for {sdata}.\n")
    time.sleep(1)

    # Second check of TX counter
    tx2 = checkCounters(headers, portName)

    # Visual debug of TX1 and TX2 counters
    print("TX Counters")
    print(f"tx1: {tx1}")
    print(f"tx2: {tx2}\n")

    # Timeout timer
    time.sleep(args.t)

    # Compare counters to determine console logout
    if tx1 == tx2:
        print(f"tx1=tx2 for 10s. Console timeout...\n")
        syslog.syslog("Inactivity on active session detected.")
        time.sleep(2)
        deviceLogout(sdata)
    else:
        print(f"tx1<tx2. No timeout...starting over...\n")
        syslog.syslog(f"Activity on active session detected on {sdata}.")
        time.sleep(2)
        timeoutCheck(headers, sdata, portName)

# Send logout commands via serial to end device
def deviceLogout(sdata):

    os.system(f"pmchat -e -Sv -t 10 '' '\r\n\dexit\rexit\rexit' < /dev/serial/by-opengear-id/{sdata} 2>&1")
    syslog.syslog("Console timeout issued.")

    
if __name__ == "__main__":
     
    syslog.syslog("Port timeout script initiated.")

    print(f"\n\nOpengear Serial Port Timeout Script, Version {v}\n")
    print(GNU)

    headers = createToken()
    
    sdata = checkSessions(headers)
