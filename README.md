# fault-tolerant-2pc-protocol
A fault-tolerant implementation of the Two-Phase Commit (2PC) protocol in a distributed system, simulating coordinator and participant node failures to ensure transaction atomicity and consistency.


## Overview
This program is compiled and run using python version 3.12.2 on MACOSX

## Requirements/Libraries used
xmlrpc module 
sys
time
json


## How to run
### Step 1:
Open terminal/cmd:
Run the 2 participants first in different terminals:	
python participant_server_1.py
python participant_server_2.py

### Step 2:
In a different terminal/cmd:
Run the co-ordinator:
python transaction_coordinator.py


### After running overview:
##Note: After any prepare message is sent from the transaction coordinator, always check participants server in the terminal to respond "1" for "yes" and "2" for "no", to select if the participant wants to respond as "yes" to commit the transaction or "no" to abort the transaction.

### Part 1:
-Select option 1 from the menu : The coordinator fails before sending the prepare message and participants respond with "No message recieved, co-ordinator may be down"
-Select option 2 from the menu : The coordinator sends the prepare message to the partipants and participants respond with "no"
-- The coordinator aborts the transaction

### Part 2:
-Select option 2 from the menu : The coordinator sends a prepare message to the participants. If the both the particiapants respond with "yes" the transaction is commited, or else the it is aborted.

### Part 3:
-Select option 3 from the menu : The coordinator stores  the transaction information on disk before sending the commit mesaage.It fails after sending a prepare message to one of the participants. The co-ordinator restarts and and continues by completing the transactions by commiting after everything up.

### Part 4:
-Select option 4 from the menu : The coordinator receives "yes" notification, the node fails. The participant task is killed and coordinator is restarted. After restarting, it checks for previous transactions if present, and commits them. If messages received from particiapnt is "no", transaction is aborted.


### Exit : 
Select option 5 to exit the transaction co-ordinator. 
Press "Ctrl+C" to exit the participant servers 1 and 2 respectively.
