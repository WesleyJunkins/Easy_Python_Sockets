import asyncio
from ws_server import ws_server

# Step 1: define the handlers for your server.
#         I.e. When an object is sent with a method name, create a function to be run when that message is received.
async def set_background_color(m):
    print(f"[Server] Set background color to {m['params']['color']}.")

async def say(m):
    print(m['params']['text'])

handlers = {
    "set-background-color": set_background_color,
    "say": say
}

# Step 2: create a new server.
#         Include the value of the port on which you want to listen, as well as the handlers object you just created.
#         Beyond this, the server is running.
myNewServer = ws_server(3000, handlers)
myNewServer.set_list_mode(True)
myNewServer.set_broadcastable(True)
myNewServer.set_debug_mode(True)
myNewServer.set_probe_mode(True, 3000)

# Step 3: write code to interact with client(s).
#         Define a function to broadcast a message to clients every 5 seconds. The message that is broadcast is the SAY method and the text you would like to say
async def broadcast_messages():
    while True:
        await myNewServer.broadcast_message("say", {"text": "This was broadcast from the server. The next one happens in 5 secs."})
        await asyncio.sleep(5)

async def main():
    server_task = asyncio.create_task(myNewServer.start_server())
    broadcast_task = asyncio.create_task(broadcast_messages())
    await asyncio.gather(server_task, broadcast_task)

if __name__ == "__main__":
    asyncio.run(main())
