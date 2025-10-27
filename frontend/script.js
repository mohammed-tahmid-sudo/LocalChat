// const ws = new WebSocket("ws://localhost:8080");

// let userId;        // store user id globally
// let list_users = []; // store contacts globally

// ws.onopen = () => {
//   ws.send(JSON.stringify({ type: "contact" }));
// };

// ws.onmessage = (e) => {
//   console.log("From server:", e.data);
//   if (e.data) {
//     const message = JSON.parse(e.data);

//     if (message.type === "user_id") {
//       userId = message.user_id;  // get userId from server
//       document.cookie = `user_id=${userId}; loggedin=true; path=/; max-age=86400`;
//       console.log(document.cookie);
//     } else if (message.type === "contact") {
//       list_users = message.contacts;
//       console.log("Contacts:", list_users);
//     }
//   }
// };
const ws = new WebSocket("ws://localhost:8080");

const userListDiv = document.getElementById("user-list");
const contentDiv = document.querySelector(".content");

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "contact" }));
};

ws.onmessage = (e) => {
  const regex = /\('(.+?)',\s*(\d+)\)/g;
  const users = [];
  let match;
  while ((match = regex.exec(e.data)) !== null) {
    users.push({ name: match[1], id: match[2] });
  }

  // Update sidebar
  userListDiv.innerHTML = "";
  users.forEach(u => {
    const div = document.createElement("div");
    div.className = "menu-item";
    div.textContent = u.name;
    div.onclick = () => {
      contentDiv.innerHTML = `<h1>${u.name}</h1><p>Chatting with ${u.name}</p>`;
    };
    userListDiv.appendChild(div);
  });
};
