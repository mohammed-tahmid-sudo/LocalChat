import WebSocket from "ws";
import fs from "fs";
import readline from "readline";

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function ask(q) {
  return new Promise((res) => rl.question(q, res));
}

const ws = new WebSocket("ws://127.0.0.1:12345");

let userdata = null;

ws.on("open", async () => {
  if (fs.existsSync("userdata.json")) {
    userdata = JSON.parse(fs.readFileSync("userdata.json"));
    sendPing(userdata.id);
    handleMessaging();
  } else {
    const name = await ask("Enter your name: ");
    createUser(name);
  }
});

function sendPing(id) {
  setInterval(() => {
    ws.send(JSON.stringify({ type: "ping", id }));
  }, 5000);
}

function createUser(name) {
  const data = { type: "create_user", name };
  ws.send(JSON.stringify(data));
}

function handleMessaging() {
  ws.send(JSON.stringify({ type: "contact" }));
}

ws.on("message", async (msg) => {
  try {
    const data = JSON.parse(msg.toString());

    if (data.type === "create_user_reply" || data.id) {
      fs.writeFileSync("userdata.json", JSON.stringify(data, null, 2));
      userdata = data;
      console.log("User created.");
      sendPing(data.id);
      handleMessaging();
    }

    if (data.type === "contact_list") {
      console.log("Contacts:", data.users);
      const id = await ask("Select user ID: ");
      chatLoop(id);
    }

    if (data.type === "message") {
      console.log(`From ${data.sender}: ${data.message}`);
    }
  } catch {
    console.log("Received:", msg.toString());
  }
});

async function chatLoop(toId) {
  while (true) {
    const inp = await ask("Enter your message (@lu to list users): ");
    if (inp === "@lu") {
      ws.send(JSON.stringify({ type: "contact" }));
      continue;
    }
    ws.send(
      JSON.stringify({
        type: "message",
        sender: userdata.id,
        reciver: toId,
        message: inp,
      })
    );
  }
}
