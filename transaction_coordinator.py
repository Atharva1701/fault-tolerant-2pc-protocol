from dataclasses import dataclass, field
import json
from pathlib import Path
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import time
import sys
from typing import Dict, List, Callable
from functools import partial

P_CNT = 2
STAT = [False, False]
PORTS = [5001, 5002]



def countdown_timer(seconds: int) -> None:
    for i in range(seconds, 0, -1):
        print(f"Waiting... {i} seconds remaining ", end='\r')
        time.sleep(1)
    print("\nProceeding....") 


@dataclass
class LogData:
    status: Dict[int, str] = field(default_factory=lambda: {0: "Active", 1: "Active"})
    transaction_status: str = "Active"

class Transaction_Coordinator:
    def __init__(self, port: int, add: str) -> None:
        self.address = add
        self.port = port
        self.alive = True
        self.trans_data: Dict[str, str] = {}
        self.users: List[xmlrpc.client.ServerProxy] = []
        self.u_response: List[str] = ['' for _ in range(P_CNT)]
        self.server = SimpleXMLRPCServer((add, port))

    def start_transaction(self, opt: str) -> None:
        handlers: Dict[str, Callable[[], None]] = {
            '1': self.fail_coordinator_before_prepare,
            '2': partial(self.activate_transaction,'2'),
            '3': partial(self.activate_transaction,'3'),
            '4': partial(self.activate_transaction,'4'),
            '5': self.shutdown
        }
        handler = handlers.get(opt, lambda: print("Invalid option selected"))
        handler()

    def activate_transaction(self,opt) -> None:
        if(opt=='2' or opt=='3' or opt=='4'):
            self.trans_data = {'status': {0: "Active", 1: "Active"}, 'transaction_status': "Active"}
            self.start_update(self.trans_data)
            self.alive = True
            self.handle_participant_responses(opt)
        

    def handle_participant_responses(self,opt) -> None:
        for id in range(P_CNT):
            try:
                self.u_response[id] = self.users[id].msg("Prepare")
                print(f"Participant-{id + 1} has responded with: {self.u_response[id]}")
            except:
                continue

        if any(reply == '' for reply in self.u_response):
            self.auto_abort()
        elif all(reply == "yes" for reply in self.u_response):
            self.initiate_commit(opt)
        elif any(reply == "no" for reply in self.u_response):
            self.initiate_abort()

    def fail_coordinator_before_prepare(self) -> None:
        print("====================================================================================================================")
        print("Failing Co-ordinator Before sending Prepare Notification")
        self.alive = False
        print("====================================================================================================================")
        # countdown_timer(5)

    def auto_abort(self) -> None:
        print("Initiating Abort for the Transaction... One or More Participants Unresponsive!")
        self.trans_data.update({'status': {0: "Abort", 1: "Abort"}, 'transaction_status': 'Aborted'})
        self.start_update(self.trans_data)
        print("====================================================================================================================")
        print('The Current Transaction has been Aborted and Logs have been successfully Updated')
        print("====================================================================================================================")
        self.notify_participants("Abort")

    def initiate_commit(self,opt) -> None:
        try:
            self.handle_commit_scenarios(opt)
        except Exception as e:
            print(e)
            print(f"The Failure of the Participant-{id} has been detected... Please Wait until the participant is up again")
        if all(status == "Commit" for status in self.trans_data['status'].values()):
            self.trans_data['transaction_status'] = 'Completed'
            self.start_update(self.trans_data)
            print("Successfully Completed the Transaction")
            print("====================================================================================================================")

    def handle_commit_scenarios(self, opt: str = '') -> None:
        print("====================================================================================================================")
        print("Response Recieved From All the Paticipants...Initializing Commit for the Transaction")
        for id in range(P_CNT):
            try:
                if id and opt == '3':
                    print("After sending commit for one participant the co-ordinator has failed.....The Co-ordinator is Restarting.") 
                    print("====================================================================================================================")
                    # countdown_timer(12)
                elif id and opt == '4':
                    print(" One participant node has failed after the participant responded yes...Killing participant task and restarting")
                    print("====================================================================================================================")
                    # countdown_timer(12)
                else:
                    self.users[id].msg("Commit")
                    self.trans_data['status'][id]=="Commit"
                    self.start_update(self.trans_data)
            except  Exception as e:
                print(e)
                print("The Failure of the Participant-"+ str(id)+" has been detected...Please Wait until the participant is up again")
        if(all(status=="Commit"for status in self.trans_data['status'].values())):
            self.trans_data['transaction_status']= 'Completed'
            self.start_update(self.trans_data)
            print("Successfully Completed the Transaction")
            print("====================================================================================================================")

    def initiate_abort(self) -> None:
        print("====================================================================================================================")
        print("Initiating Abort for the Transaction... One or More Participants has Responded as \"no\"!")
        self.notify_participants("Abort")
        self.trans_data.update({'status': {0: "Abort", 1: "Abort"}, 'transaction_status': 'Aborted'})
        self.start_update(self.trans_data)
        print("The Transaction has been Aborted....")
        print("====================================================================================================================")

    def notify_participants(self, message: str) -> None:
        for id in range(P_CNT):
            try:
                self.users[id].msg(message)
            except Exception as e:
                print(f"Awaiting the response from participant {id + 1} as it is currently unresponsive.....")

    def start_check(self) -> None:
        print("Please Wait... Previous Transaction Being Evaluated")
        if not self.trans_data:
            self.trans_data = {'status': {0: "Active", 1: "Active"}, 'transaction_status': "Active"}
        else:
            self.check_and_commit()
        print("Previous Status Check for Transaction Completed.")

    def check_and_commit(self) -> None:
        commit_attempted = False
        participant_range = range(P_CNT)

        def commit_participant(id):
            if (status := self.trans_data['status'][id]) == "Active":
                print(f"Initiating Commit Message transmission to Participant-{id + 1}")
                self.users[id].msg("Commit")
                self.trans_data['status'][id] = "Commit"
                nonlocal commit_attempted
                commit_attempted = True
                self.start_update(self.trans_data)

        def handle_failure(id, exception):
            print(f"Failure for Participant-{id + 1}, Awaiting participant Response: {exception}")

        for id in participant_range:
            try:
                commit_participant(id)
            except Exception as e:
                handle_failure(id, e)

        all_committed = all(status == 'Commit' for status in self.trans_data['status'].values())
        self.trans_data['transaction_status'] = 'Completed' if all_committed else self.trans_data['transaction_status']

        if commit_attempted:
            print("Successfully Completed Transaction, current status has been updated to the log file.")
        
        self.start_update(self.trans_data)

    def start(self) -> None:
        print("====================================================================================================================")
        print("COORDINATOR IS RUNNING")
        print("====================================================================================================================")
        self.alive = True

        while True:
            self.trans_data = self.read_logs() or {}
            self.users = []
            self.u_response = ['' for _ in range(P_CNT)]
            participants_ready = self.initialize_users()

            if participants_ready:
                if self.check_participant_status():
                    self.display_menu()
                else:
                    print("Response from Participants Pending, Please Wait....")
            else:
                print("Response from Participants Pending, Please Wait....")
            
            countdown_timer(5)


    def initialize_users(self) -> bool:
        p_up = True
        for id in range(P_CNT):
            try:
                self.users.append(self.connection(id))
                STAT[id] = True
            except:
                STAT[id] = False
                p_up = False
        return p_up

    def check_participant_status(self) -> bool:
        all_ok = True
        if self.alive:
            for id in range(P_CNT):
                try:
                    self.users[id].msg("Alive")
                except:
                    continue
        for id in range(P_CNT):
            try:
                STAT[id] = self.users[id].alive()
            except:
                STAT[id] = False
            if not STAT[id]:
                all_ok = False
                break

        if all_ok:
            if self.alive:
                for id in range(P_CNT):
                    try:
                        self.users[id].msg("Alive")
                    except:
                        continue
            print("====================================================================================================================")
            print("All the participants performing the transactions are up")
            print("====================================================================================================================")
            self.start_check()

        return all_ok

    def display_menu(self) -> None:
        print("====================================================================================================================")
        print("Welcome To Transaction Management System ")
        print("====================================================================================================================")
        print("Please Select one of the options:")
        print("1. Fail Co-ordinator Before sending Prepare Notification")
        print("2. Send Prepare Notification to the Participants")
        print("3. After sending Commit Notification, Fail Co-ordinator ")
        print("4. After sending Yes Notification to the Co-ordinator, test node failure")
        print("5. Exit")
        print("====================================================================================================================")
        opt = input("Enter your choice (1,2,3,4 or 5): ")
        print("====================================================================================================================")
        self.start_transaction(opt)

    @staticmethod
    def connection(PID: int) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f"http://127.0.0.1:{PORTS[PID]}", allow_none=True)
    


    def read_logs(self) -> Dict:
        log_file_path = Path("log.json")

        def parse_log_file(file_path: Path) -> dict:
            with file_path.open("r") as log_file:
                return json.load(
                    log_file,
                    object_hook=lambda d: {int(k) if k.lstrip("-").isdigit() else k: v for k, v in d.items()}
                )

        def create_new_log_file() -> dict:
            print("--- Creating a new log file ---")
            log_data = {}
            self.save_logs(log_data)
            return log_data

        log_data = parse_log_file(log_file_path) if log_file_path.exists() else create_new_log_file()

        return LogData(**log_data).__dict__ if isinstance(log_data, dict) else LogData().__dict__


    @staticmethod
    def save_logs(log_data: Dict) -> None:
        with open("log.json", "w") as log_file:
            json.dump(log_data, log_file, indent=4)

    @staticmethod
    def start_update(trans_data: Dict) -> bool:
        content = json.dumps(trans_data, indent=4)
        try:
            with open("log.json", "w") as log:
                log.write(content)
            return True
        except Exception as e:
            print(f"Error writing to log: {e}")
            return False

    def shutdown(self) -> None:
        sys.exit("Shutting Down the Transaction Co-ordinator")

if __name__ == "__main__":
    tc = Transaction_Coordinator(5000, "127.0.0.1")
    try:
        tc.start()
    except KeyboardInterrupt:
        print("====================================================================================================================")
        print("The Co-ordinator is shutting down")
        print("====================================================================================================================")
