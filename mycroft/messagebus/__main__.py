#!/usr/bin/env python3
import json
import traceback
from time import sleep
from websocket import WebSocketApp


def on_message(client, message):
    message = json.loads(message)
    print(message)


def main():
    sleep(0.5)

    # Connect to the default websocket used by chatterbox-core
    url = 'ws://127.0.0.1:8181/core'
    print('Starting client on:', url)
    client = WebSocketApp(url=url, on_message=on_message)
    client.run_forever()
    print('Client stopped.')


if __name__ == '__main__':
    # Run loop trying to reconnect if there are any issues starting
    # the websocket
    while True:
        try:
            main()
        except KeyboardInterrupt:
            raise
        except:
            traceback.print_exc()
