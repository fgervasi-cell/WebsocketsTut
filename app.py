import asyncio
import json
import secrets

import websockets
from connect4 import PLAYER1, PLAYER2
from connect4 import Connect4

JOIN = {}
WATCH = {}


async def replay_moves(game, websocket):
    for move in enumerate(game.moves):
        event = {
            "type": "play",
            "player": move[1][0],
            "column": move[1][1],
            "row": move[1][2],
        }
        await websocket.send(json.dumps(event))


async def start(websocket):
    # Initialize a Connect Four game, the set of WebSocket connections
    # receiving moves from this game, and secret access token
    game = Connect4()
    connected = {websocket}

    join_key = secrets.token_urlsafe(12)
    watch_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected
    WATCH[watch_key] = game, connected

    try:
        # Send the secret access token to the browser of the first player,
        # where it'll be used for building a "join" link.
        event = {
            "type": "init",
            "join": join_key,
            "watch": watch_key,
        }
        await websocket.send(json.dumps(event))

        print("first player started game", id(game))
        async for message in websocket:
            await play(websocket, game, PLAYER1, connected)
            print("first player sent", message)

    finally:
        del JOIN[join_key]


async def handler(websocket, path):
    # Receive and parse the "init" event from the UI.
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"

    if "join" in event:
        # Second player joins an exisiting game.
        await join(websocket, event["join"])
    elif "watch" in event:
        await watch(websocket, event["watch"])
    else:
        # First player starts a new game.
        await start(websocket)

    # First player starts a new game.
    await start(websocket)


async def watch(websocket, watch_key):
    game, connected = WATCH[watch_key]
    connected.add(websocket)
    await replay_moves(game, websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected.remove(websocket)


async def error(websocket, message):
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))


async def join(websocket, join_key):
    # Find the Connect Four Game
    try:
        game, connected = JOIN[join_key]
    except KeyError:
        await error(websocket, "Game not found.")
        return

    # Register to receive moves from this game.
    connected.add(websocket)

    try:
        print("second player joined game", id(game))
        async for message in websocket:
            await play(websocket, game, PLAYER2, connected)
            print("second player sent", message)
    finally:
        connected.remove(websocket)


async def play(websocket, game, player, connected):
    async for message in websocket:
        data = json.loads(message)
        assert data["type"] == "play"
        try:
            row = game.play(player, data["column"])
            play_move = {
                "type": "play",
                "player": player,
                "column": data["column"],
                "row": row,
            }
            websockets.broadcast(connected, json.dumps(play_move))
            if game.winner is not None:
                winner = {
                    "type": "win",
                    "player": player
                }
                websockets.broadcast(connected, json.dumps(winner))
        except RuntimeError as e:
            await error(websocket, str(e))


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
