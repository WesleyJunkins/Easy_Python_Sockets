import asyncio
import json
import uuid
import websockets

class ws_client:
    def __init__(self, ws_host, ws_port, handlers):
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.handlers = handlers
        self.debugMode = False
        self.listMode = False
        self.dummyBool = False
        self.refreshID = str(uuid.uuid4())
        self.clientID = {
            'id': str(uuid.uuid4()),
            'refreshID': self.refreshID,
            'host': ws_host,
            'port': ws_port,
        }
        self.defaultHandlers = {
            "server_accepted_connect": self.server_accepted_connect,
            "server_probe": self.server_probe,
            "client_request_connect": self.client_request_connect
        }
        self.websocket = None

    async def connect(self):
        uri = f"ws://{self.ws_host}:{self.ws_port}/ws"
        self.websocket = await websockets.connect(uri)
        await self.send_message("client_request_connect", self.clientID)

    async def handle_messages(self):
        async for message in self.websocket:
            try:
                m = json.loads(message)
                await self.handle_message(m)
            except json.JSONDecodeError:
                if self.debugMode:
                    print("[Client] Message is not parseable to JSON.")

    async def handle_message(self, m):
        method = m.get('method')
        if method:
            handler = self.handlers.get(method) or self.defaultHandlers.get(method)
            if handler:
                await handler(m)
            elif self.debugMode:
                print(f"[Client] No handler defined for method {method}.")

    async def send_message(self, method, parameters):
        newMessage = json.dumps({
            'method': method,
            'params': parameters
        })
        await self.websocket.send(newMessage)
        if self.debugMode:
            print(f"[Client] Message sent to server: \n\t{newMessage}")

    async def server_accepted_connect(self, m):
        if m['params']['sendToUUID'] == self.clientID['id']:
            self.refreshID = m['params']['firstRefreshID']
            if self.debugMode:
                print("[Client] Connection to WebSocket Server was opened.")
            if self.listMode:
                print("-----------------------------------")
                print("----------| Server Info |----------")
                print(f"id: {m['params']['id']}")
                print(f"refreshID: {m['params']['firstRefreshID']}")
                print(f"port: {m['params']['port']}")
                print(f"current clients: {m['params']['numClients']}")
                print("-----------------------------------")
                print("-----------------------------------")
            await self.send_message("client_return_probe", {
                'refreshID': m['params']['firstRefreshID'],
                'id': self.clientID['id'],
                'serverID': m['params']['id']
            })

    async def server_probe(self, m):
        if self.ws_port == m['params']['port']:
            await self.send_message("client_return_probe", {
                'refreshID': m['params']['refreshID'],
                'id': self.clientID['id'],
                'serverID': m['params']['id']
            })
    
    async def client_request_connect(self, m):
        self.dummyBool = True

    def set_debug_mode(self, debugMode):
        self.debugMode = debugMode

    def set_list_mode(self, listMode):
        self.listMode = listMode
