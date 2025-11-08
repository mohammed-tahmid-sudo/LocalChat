const socket = new WebSocket("ws://0.0.0.0:8080");

// when connected
socket.addEventListener("open", () => {
  console.log("Connected");
  socket.send("Hello Server!");
});

// when receiving a message
socket.addEventListener("message", (event) => {
  console.log("Message from server:", event.data);
});

// when closed
socket.addEventListener("close", () => {
  console.log("Disconnected");
});

// when error occurs
socket.addEventListener("error", (err) => {
  console.error("WebSocket error:", err);
});
