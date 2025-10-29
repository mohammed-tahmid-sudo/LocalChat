const ws = new WebSocket("ws://localhost:8080");

let userId; // store user id globally
let list_users = []; // store contacts globally

ws.onopen = () => {
  if (user)
};

ws.onmessage = (e) => {
  console.log("From server:", e.data);
  // if (e.data) {
  //   const message = JSON.parse(e.data);

  //   if (message.type === "contact") {
  //     list_users = message.contacts;
  //     console.log("Contacts:", list_users);
  //   } else if (message.type === "contact") {
  //     userId = message.user_id; // get userId from server
  //     document.cookie = `user_id=${userId}; loggedin=true; path=/; max-age=86400`;
  //     console.log(document.cookie);
  //   }
  // }
};
