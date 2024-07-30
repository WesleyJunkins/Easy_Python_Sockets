import asyncio
from ws_client import ws_client

# Step 1: define the handlers for your client.
# I.e. When an object is sent with a method name, create a function to be run when that message is received.
async def set_background_color(m):
    print(f"[Client] Set background color to {m['params']['color']}.")

async def say(m):
    print(m['params']['text'])

handlers = {
    "set-background-color": set_background_color,
    "say": say
}

# Step 2: create a new client.
# Include the value of the host, port, and the handlers object you just created.
# Beyond this, the client is running.
myNewClient = ws_client("localhost", 3000, handlers)
myNewClient.set_list_mode(True)
myNewClient.set_debug_mode(True)

# Step 3: write code to interact with a server.
async def send_messages():
    while True:
        await myNewClient.send_message("say", {"text": "This was broadcast from the client. The next one happens in 6 secs."})
        await asyncio.sleep(6)

async def main():
    await myNewClient.connect()
    handle_messages_task = asyncio.create_task(myNewClient.handle_messages())
    send_messages_task = asyncio.create_task(send_messages())
    await asyncio.gather(handle_messages_task, send_messages_task)

if __name__ == "__main__":
    asyncio.run(main())
