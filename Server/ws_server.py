import asyncio
import json
import uuid
from websockets import serve

class ws_server:
    def __init__(self, server_port, handlers):
        self.server_port = server_port
        self.handlers = handlers
        self.broadcastable = False
        self.debugMode = False
        self.listMode = False
        self.probeMode = False
        self.probeInterval = 10  # in seconds
        self.refreshID = str(uuid.uuid4())
        self.clientList = []
        self.serverID = {
            'id': str(uuid.uuid4()),
            'port': server_port,
            'numClients': 0
        }
        self.defaultHandlers = {
            "client_request_connect": self.client_request_connect,
            "client_return_probe": self.client_return_probe
        }
        self.connected_clients = set()

    async def start_server(self):
        self.server = await serve(self.handler, "localhost", self.server_port)
        if self.debugMode:
            print(f"[Server] Created a Web Socket server on port {self.server_port}.")
        if self.probeMode:
            asyncio.create_task(self.probe_clients())
        await asyncio.Future()  # Run forever

    async def handler(self, websocket, path):
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                await self.handle_message(message, websocket)
        finally:
            self.connected_clients.remove(websocket)

    async def handle_message(self, message, websocket):
        try:
            m = json.loads(message)
            method = m.get('method')
            params = m.get('params')
            if method:
                if method in self.handlers:
                    await self.handlers[method](m)
                elif method in self.defaultHandlers:
                    await self.defaultHandlers[method](m)
                elif self.debugMode:
                    print(f"[Server] No handler defined for method {method}.")
        except json.JSONDecodeError:
            if self.debugMode:
                print("[Server] Message is not parseable to JSON.")

        if self.broadcastable:
            await self.broadcast_message(method, params, websocket)

    async def broadcast_message(self, method, params, websocket=None):
        message = json.dumps({"method": method, "params": params})
        if self.debugMode:
            print(f"[Server] Sending message: {message}")

        for client in self.connected_clients:
            if client != websocket and client.open:
                await client.send(message)
                if self.debugMode:
                    print(f"[Server] Message broadcast to clients: \n\t{message}")

    def set_broadcastable(self, broadcastable):
        self.broadcastable = broadcastable

    def set_debug_mode(self, debugMode):
        self.debugMode = debugMode

    def set_list_mode(self, listMode):
        self.listMode = listMode

    def set_probe_mode(self, probeMode, probeInterval=None):
        self.probeMode = probeMode
        if probeMode and probeInterval:
            self.probeInterval = probeInterval

    async def client_request_connect(self, m):
        self.clientList.append(m['params'])
        if self.debugMode:
            print("[Server] A client connected.")

        if self.listMode:
            print("-----------------------------------")
            print("----------| Client List |----------")
            print(self.clientList)
            print("-----------------------------------")
            print("-----------------------------------")

        self.serverID['numClients'] += 1
        await self.broadcast_message(
            method='server_accepted_connect',
            params={
                'id': self.serverID['id'],
                'port': self.serverID['port'],
                'numClients': self.serverID['numClients'],
                'sendToUUID': m['params']['id'],
                'firstRefreshID': self.refreshID
            }
        )

    async def client_return_probe(self, m):
        updateClientIndex = next((i for i, client in enumerate(self.clientList) if client['id'] == str(m['params']['id']).strip()), None)
        if updateClientIndex is not None:
            self.clientList[updateClientIndex]['refreshID'] = self.refreshID

    async def probe_clients(self):
        while True:
            await asyncio.sleep(self.probeInterval)
            somethingWasRemoved = False
            for client in self.clientList[:]:
                if client.get('refreshID') != self.refreshID:
                    client['warningNumber'] += 1
                    self.clientList.remove(client)
                    self.serverID['numClients'] -= 1
                    somethingWasRemoved = True

            self.refreshID = str(uuid.uuid4())
            await self.broadcast_message(
                method='server_probe',
                params={
                    'refreshID': self.refreshID,
                    'id': self.serverID['id'],
                    'port': self.serverID['port']
                }
            )

            if somethingWasRemoved and self.listMode:
                print("-----------------------------------")
                print("----------| Client List |----------")
                print(self.clientList)
                print("-----------------------------------")
                print("-----------------------------------")
