const items = [
  { name: "name1", img: "img1.jpg", message: "message1" },
  { name: "name2", img: "img2.jpg", message: "message2" },
  { name: "name3", img: "img3.jpg", message: "message3" },
  { name: "name4", img: "img4.jpg", message: "message4" },
  { name: "name5", img: "img5.jpg", message: "message5" },
  { name: "name6", img: "img6.jpg", message: "message6" },
  { name: "name7", img: "img7.jpg", message: "message7" },
];

const container = document.getElementById("container");

items.forEach((item) => {
  const box = document.createElement("div");
  box.className = "item-box";

  const img = document.createElement("img");
  img.src = item.img;

  const title = document.createElement("h3");
  title.textContent = item.name;

  const desc = document.createElement("p");
  desc.textContent = item.message;

  box.append(img, title, desc);
  container.appendChild(box);
});
