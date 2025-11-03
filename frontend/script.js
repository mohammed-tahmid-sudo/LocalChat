// Frontend script: connect to backend via WebSocket with HTTP fallback, handle messages and UI.

(() => {
	// Configuration: can set <body data-ws-url="ws://localhost:8080/ws" data-rest-url="/api/chat">
	const wsUrl = document.body.dataset.wsUrl || "ws://localhost:8080/ws";
	const restUrl = document.body.datasetRestUrl || document.body.dataset.restUrl || "/api/chat";

	// UI elements (IDs expected in the page)
	const elMessages = document.getElementById("chatMessages");
	const elInput = document.getElementById("chatInput");
	const elSend = document.getElementById("sendBtn");
	const elStatus = document.getElementById("status");

	// Connection state
	let socket = null;
	let connected = false;
	let reconnectAttempts = 0;
	const maxReconnectDelay = 30000;
	const outgoingQueue = [];

	function logStatus(text, cls) {
		if (elStatus) {
			elStatus.textContent = text;
			elStatus.className = cls || "";
		}
		console.debug("[chat] " + text);
	}

	function renderMessage(msg, from = "server") {
		if (!elMessages) return;
		const div = document.createElement("div");
		div.className = "message " + (from === "user" ? "user" : "server");
		const time = new Date().toLocaleTimeString();
		div.textContent = `[${time}] ${msg}`;
		elMessages.appendChild(div);
		elMessages.scrollTop = elMessages.scrollHeight;
	}

	function flushQueue() {
		while (outgoingQueue.length && connected) {
			const m = outgoingQueue.shift();
			_sendViaSocket(m);
		}
	}

	function _sendViaSocket(payload) {
		if (!socket || socket.readyState !== WebSocket.OPEN) {
			// shouldn't happen if connected flag is accurate, but re-queue
			outgoingQueue.unshift(payload);
			return;
		}
		try {
			socket.send(JSON.stringify(payload));
		} catch (err) {
			console.error("Failed to send via socket:", err);
			outgoingQueue.unshift(payload);
		}
	}

	function sendMessage(text) {
		if (!text || !text.trim()) return;
		const payload = { type: "message", text: text.trim() };
		renderMessage(payload.text, "user");

		if (connected && socket && socket.readyState === WebSocket.OPEN) {
			_sendViaSocket(payload);
		} else {
			// queue and try REST fallback immediately
			outgoingQueue.push(payload);
			tryRestSend(payload);
		}
	}

	function tryRestSend(payload) {
		if (!restUrl) return;
		fetch(restUrl, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
		})
			.then(res => {
				if (!res.ok) throw new Error("REST send failed: " + res.status);
				return res.json().catch(() => null);
			})
			.then(data => {
				// If server returns an immediate reply, show it
				if (data && data.reply) {
					renderMessage(data.reply, "server");
				}
			})
			.catch(err => {
				console.warn("REST send error:", err);
			});
	}

	function createWebSocket() {
		if (!("WebSocket" in window)) {
			logStatus("WebSocket not supported, using HTTP fallback", "warn");
			return;
		}

		try {
			socket = new WebSocket(wsUrl);
		} catch (err) {
			console.warn("WebSocket constructor failed, will use HTTP fallback:", err);
			return;
		}

		socket.addEventListener("open", () => {
			connected = true;
			reconnectAttempts = 0;
			logStatus("Connected", "ok");
			flushQueue();
		});

		socket.addEventListener("message", (ev) => {
			// Expect server JSON like { type: "message", text: "..." } or plain text
			let data = null;
			try { data = JSON.parse(ev.data); } catch (_) { data = ev.data; }
			if (data && data.type === "message" && data.text) {
				renderMessage(data.text, "server");
			} else {
				renderMessage(typeof data === "string" ? data : JSON.stringify(data), "server");
			}
		});

		socket.addEventListener("close", (ev) => {
			connected = false;
			socket = null;
			logStatus("Disconnected, reconnecting...", "warn");
			scheduleReconnect();
		});

		socket.addEventListener("error", (err) => {
			console.error("WebSocket error:", err);
			// Let close event handle reconnect
		});
	}

	function scheduleReconnect() {
		reconnectAttempts++;
		const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), maxReconnectDelay);
		setTimeout(() => {
			logStatus("Reconnecting...", "warn");
			createWebSocket();
		}, delay);
	}

	// UI wiring
	if (elSend) {
		elSend.addEventListener("click", () => {
			if (!elInput) return;
			const text = elInput.value;
			sendMessage(text);
			elInput.value = "";
			elInput.focus();
		});
	}

	if (elInput) {
		elInput.addEventListener("keydown", (e) => {
			if (e.key === "Enter" && !e.shiftKey) {
				e.preventDefault();
				if (elSend) elSend.click();
			}
		});
	}

	// Try to open WS immediately
	createWebSocket();

	// Periodic polling fallback: poll REST for new messages if WS not connected
	let pollInterval = 3000;
	let pollTimer = null;
	function startPolling() {
		if (pollTimer) return;
		pollTimer = setInterval(() => {
			if (connected || !restUrl) return;
			fetch(restUrl, { method: "GET" })
				.then(r => r.json().catch(() => null))
				.then(data => {
					if (!data) return;
					// server may return { messages: [...] } or { reply: "..." }
					if (Array.isArray(data.messages)) {
						data.messages.forEach(m => renderMessage(m, "server"));
					} else if (data.reply) {
						renderMessage(data.reply, "server");
					}
				})
				.catch(() => {});
		}, pollInterval);
	}

	function stopPolling() {
		if (!pollTimer) return;
		clearInterval(pollTimer);
		pollTimer = null;
	}

	// Start polling only if WebSocket isn't connected after a short timeout
	setTimeout(() => {
		if (!connected) startPolling();
	}, 1000);

	// Expose basic API to window for debugging
	window.localChat = {
		sendMessage,
		renderMessage,
		getStatus: () => ({ connected, wsUrl, restUrl }),
	};

	// ...existing code...
})();