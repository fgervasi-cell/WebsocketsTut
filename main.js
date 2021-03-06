import { createBoard, playMove} from "./connect4.js";

window.addEventListener("DOMContentLoaded", () => {
   // Initialize the UI.
   const board = document.querySelector(".board");
   createBoard(board);
   // Open the WebSocket connection and register event handlers.
   const websocket = new WebSocket(getWebSocketServer());
   initGame(websocket);
   receiveMoves(board, websocket);
   sendMoves(board, websocket);
});

function getWebSocketServer()
{
   if (window.location.host === "fgervasi-cell.github.io")
   {
      return "wss://websockets-tut.herokuapp.com/";
   }
   else if (window.location.host === "localhost:8000")
   {
      return "ws://localhost:8001/";
   }
   else
   {
      throw new Error(`Unsupported host: ${window.location.host}`);
   }
}

function sendMoves(board, websocket)
{
   // When clicking a column, send a "play" event for a move in that column.
   board.addEventListener("click", ({target}) => {
      const column = target.dataset.column;
      // Ignore clicks outside a column.
      if (column === undefined || window.location.href.indexOf("watch") > -1)
      {
         return;
      }
      const event = {
         type: "play",
         column: parseInt(column, 10),
      };
      websocket.send(JSON.stringify(event));
   });
}

function showMessage(message)
{
   window.setTimeout(() => window.alert(message), 50);
}

function  receiveMoves(board, websocket)
{
   websocket.addEventListener("message", ({data}) => {
      const event = JSON.parse(data);
      switch (event.type)
      {
         case "play":
               // Update the UI with the move.
              playMove(board, event.player, event.column, event.row);
              break;
         case "win":
            showMessage(`Player ${event.player} wins!`);
            // No further messages are expected; close the WebSocket connection.
            websocket.close(1000);
         case "error":
            showMessage(event.message);
            break;
         case "init":
            // Create link for inviting the second player.
            document.querySelector(".join").href = "?join=" + event.join;
            document.querySelector(".watch").href = "?watch=" + event.watch;
            break;
         default:
            throw new Error(`Unsupported event type: ${event.type}.`);
      }
   });
}

function initGame(websocket)
{
   websocket.addEventListener("open", () => {
      // Send an "init" event for the first player.
      const params = new URLSearchParams(window.location.search);
      let event = { type: "init" };
      if (params.has("join"))
      {
         // Second player joins an existing game
         event.join = params.get("join");
      }

      if (params.has("watch"))
      {
         event.watch = params.get("watch");
      }
      websocket.send(JSON.stringify(event));
   });
}