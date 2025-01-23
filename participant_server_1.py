from threading import Timer
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client

class ServerP1:
    def __init__(self, c_port: int, host: str, p_port: int) -> None:
        self.server = self.create_server(host, p_port)
        self.timing = None
        self.register_functions()
        self.coordinator_proxy = self.create_coordinator_proxy(host, c_port)
        self.t_prepared = True

    def create_server(self, host: str, p_port: int) -> SimpleXMLRPCServer:
        return SimpleXMLRPCServer((host, p_port))

    def register_functions(self) -> None:
        self.server.register_function(self.isAliveHandler, 'alive')
        self.server.register_function(self.message_handler, 'msg')

    def create_coordinator_proxy(self, host: str, c_port: int) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f'http://{host}:{c_port}')

    def start(self):
        try:
            self.display_server_status("Running")
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.display_server_status("Shut Down")

    def display_server_status(self, status):
        print("====================================================================================================================")
        print(f"The Participant-1 Server is {status} ")
        print("====================================================================================================================")

    def prepare_message_handler(self) -> str:
        def set_prepared() -> str:
            self.t_prepared = True
            return "no"

        def get_reply() -> str:
            return self.retrieve_reply()

        return set_prepared() if not self.t_prepared else get_reply()

    def begin_timer(self, callback, duration: int) -> None:
        def create_timer() -> Timer:
            return Timer(duration, callback)

        self.timing = create_timer()
        self.timing.start()

    def message_handler(self, msg):
        handlers = {
            "Abort": self.handle_abort,
            "Alive": self.handle_alive,
            "Prepare": self.prepare_message_handler,
            "Commit": self.handle_commit
        }
        handler = handlers.get(msg, lambda: None)
        return handler()

    def handle_abort(self):
        print("Notification has been received for Aborting the transaction")
        self.display_separator()
        self.terminate_timer()
        return True

    def handle_alive(self):
        self.terminate_timer()
        return True

    def handle_commit(self):
        print("Notification has been received for Committing the transaction")
        self.display_separator()
        self.terminate_timer()
        return True

    def display_separator(self):
        print("====================================================================================================================")

    def display_menu(self):
        self.display_separator()
        print("Select From the Below Options:")
        self.display_separator()
        print("1. Send commit message to TC (yes)")
        print("2. Send abort message (no)")
        self.display_separator()

    def get_user_choice(self):
        while True:
            self.display_menu()
            choice = input("Enter your choice (1 or 2): ")
            if choice in ['1', '2']:
                return choice
            print("Invalid choice. Please enter 1 or 2.")

    def execute_choice(self, choice):
        response = 'yes' if choice == '1' else 'no'
        self.terminate_timer()
        return response

    def timeout_event_handler(self):
        print("====================================================================================================================")
        print("No Message Received! The Coordinator may be down.")
        self.t_prepared = False
        self.display_separator()

    def retrieve_reply(self):
        choice = self.get_user_choice()
        return self.execute_choice(choice)

    def terminate_timer(self):
        if self.timing:
            try:
                self.timing.cancel()
            except Exception as e:
                print(f"Error cancelling timer: {e}")

    def isAliveHandler(self):
        self.begin_timer(self.timeout_event_handler, 1)
        return True

if __name__ == "__main__":
    p1 = ServerP1(5000, "127.0.0.1", 5001)
    p1.start()
