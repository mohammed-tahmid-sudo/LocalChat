const ws = new WebSocket("ws://localhost:8080");

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "create_user", name: "Tahmid" }));
};

ws.onmessage = (e) => {
  console.log("From server:", e.data);
};
