// server.cpp
// Full feature-for-feature port of your Python LocalChat server to pure C++
// (POSIX sockets + sqlite3 C API).
// - No external JSON library.
// - Uses sqlite3 C API.
// - Thread-per-connection using std::thread.
// - 4-byte length-prefixed JSON messages for framing.
//
// Compile:
// g++ server.cpp -std=c++17 -pthread -lsqlite3 -O2 -o server
//
// Run:
// ./server
//
// Notes:
// - The JSON handling here is minimal but sufficient for the message shapes
// used:
//   { "type": "create_user", "name": "bob" }
//   { "type": "ping", "id": 1 }
//   { "type": "message", "sender":"1", "reciver":"2", "message":"hi" }
//   { "type": "contact" }
// - Each client thread opens its own sqlite3 connections (same as your Python
// server).
// - Database paths are the same as your Python code. Adjust if needed.

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstring>
#include <ctime>
#include <functional>
#include <iostream>
#include <map>
#include <mutex>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include <sqlite3.h>

// ---------------------- Colors ----------------------
struct Colors {
  static constexpr const char *RESET = "\033[0m";
  static constexpr const char *RED = "\033[31m";
  static constexpr const char *GREEN = "\033[32m";
  static constexpr const char *YELLOW = "\033[33m";
  static constexpr const char *BLUE = "\033[34m";
  static constexpr const char *MAGENTA = "\033[35m";
  static constexpr const char *CYAN = "\033[36m";
  static constexpr const char *WHITE = "\033[37m";
};

// ---------------------- Basic framed IO ----------------------
ssize_t write_all(int fd, const void *buf, size_t count) {
  const char *p = static_cast<const char *>(buf);
  size_t left = count;
  while (left > 0) {
    ssize_t n = send(fd, p, left, 0);
    if (n <= 0) {
      if (errno == EINTR)
        continue;
      return n;
    }
    left -= (size_t)n;
    p += n;
  }
  return (ssize_t)count;
}

ssize_t read_all(int fd, void *buf, size_t count) {
  char *p = static_cast<char *>(buf);
  size_t left = count;
  while (left > 0) {
    ssize_t n = recv(fd, p, left, 0);
    if (n <= 0) {
      if (n == 0)
        return 0; // closed
      if (errno == EINTR)
        continue;
      return n;
    }
    left -= (size_t)n;
    p += n;
  }
  return (ssize_t)count;
}

// send framed JSON: 4-byte big-endian length then payload
bool send_json_msg(int fd, const std::string &json_text) {
  uint32_t len = (uint32_t)json_text.size();
  uint32_t be = htonl(len);
  if (write_all(fd, &be, sizeof(be)) <= 0)
    return false;
  if (len > 0) {
    if (write_all(fd, json_text.data(), json_text.size()) <= 0)
      return false;
  }
  return true;
}

// receive framed JSON; returns empty optional on error or disconnect
std::optional<std::string> recv_json_msg(int fd) {
  uint32_t be;
  ssize_t r = read_all(fd, &be, sizeof(be));
  if (r == 0 || r < 0)
    return std::nullopt;
  uint32_t len = ntohl(be);
  if (len == 0)
    return std::make_optional(std::string{});
  std::string buf;
  buf.resize(len);
  ssize_t rr = read_all(fd, buf.data(), len);
  if (rr == 0 || rr < 0)
    return std::nullopt;
  return std::make_optional(std::move(buf));
}

// ---------------------- Tiny JSON (very small subset) ----------------------
// We only need to parse flat objects with string keys and string/number values.
// We'll treat all values as strings when reading for simplicity.

static inline void skip_ws(const std::string &s, size_t &i) {
  while (i < s.size() && isspace((unsigned char)s[i]))
    ++i;
}

std::string parse_json_string(const std::string &s, size_t &i) {
  // assume s[i] == '"'
  ++i;
  std::string out;
  while (i < s.size()) {
    char c = s[i++];
    if (c == '"')
      return out;
    if (c == '\\' && i < s.size()) {
      char esc = s[i++];
      switch (esc) {
      case '"':
        out.push_back('"');
        break;
      case '\\':
        out.push_back('\\');
        break;
      case '/':
        out.push_back('/');
        break;
      case 'b':
        out.push_back('\b');
        break;
      case 'f':
        out.push_back('\f');
        break;
      case 'n':
        out.push_back('\n');
        break;
      case 'r':
        out.push_back('\r');
        break;
      case 't':
        out.push_back('\t');
        break;
      default:
        out.push_back(esc);
        break;
      }
    } else {
      out.push_back(c);
    }
  }
  throw std::runtime_error("Unterminated JSON string");
}

std::string parse_json_value_as_string(const std::string &s, size_t &i) {
  skip_ws(s, i);
  if (i >= s.size())
    throw std::runtime_error("Unexpected end in value");
  if (s[i] == '"') {
    return parse_json_string(s, i);
  } else {
    // number, true, false, null, or bare token: read until , or }
    size_t start = i;
    while (i < s.size() && s[i] != ',' && s[i] != '}' &&
           !isspace((unsigned char)s[i]))
      ++i;
    return s.substr(start, i - start);
  }
}

// parse into unordered_map<string,string>
std::unordered_map<std::string, std::string>
parse_json_object(const std::string &s) {
  size_t i = 0;
  skip_ws(s, i);
  if (i >= s.size() || s[i] != '{')
    throw std::runtime_error("Not an object");
  ++i;
  std::unordered_map<std::string, std::string> out;
  skip_ws(s, i);
  if (i < s.size() && s[i] == '}')
    return out;
  while (i < s.size()) {
    skip_ws(s, i);
    if (s[i] != '"')
      throw std::runtime_error("Expected key string");
    std::string key = parse_json_string(s, i);
    skip_ws(s, i);
    if (i >= s.size() || s[i] != ':')
      throw std::runtime_error("Expected ':'");
    ++i;
    skip_ws(s, i);
    std::string val = parse_json_value_as_string(s, i);
    out[key] = val;
    skip_ws(s, i);
    if (i >= s.size())
      break;
    if (s[i] == ',') {
      ++i;
      continue;
    } else if (s[i] == '}') {
      ++i;
      break;
    } else {
      throw std::runtime_error("Expected , or }");
    }
  }
  return out;
}

// helper to escape strings for outgoing JSON
std::string json_escape(const std::string &s) {
  std::string out;
  for (char c : s) {
    switch (c) {
    case '"':
      out += "\\\"";
      break;
    case '\\':
      out += "\\\\";
      break;
    case '\b':
      out += "\\b";
      break;
    case '\f':
      out += "\\f";
      break;
    case '\n':
      out += "\\n";
      break;
    case '\r':
      out += "\\r";
      break;
    case '\t':
      out += "\\t";
      break;
    default:
      out.push_back(c);
      break;
    }
  }
  return out;
}

// build a JSON object from key->value (values already raw strings)
std::string
build_json_object(const std::vector<std::pair<std::string, std::string>> &kv) {
  std::ostringstream oss;
  oss << '{';
  bool first = true;
  for (auto &p : kv) {
    if (!first)
      oss << ',';
    first = false;
    oss << '"' << json_escape(p.first) << "\":";
    // treat as string value
    oss << '"' << json_escape(p.second) << '"';
  }
  oss << '}';
  return oss.str();
}

// ---------------------- Globals ----------------------
std::map<int, int> clients; // user_id -> socket fd
std::mutex clients_mtx;
std::atomic<bool> running{true};

// ---------------------- DB init ----------------------
void initialize() {
  sqlite3 *db = nullptr;
  if (sqlite3_open("/home/tahmid/LocalChat/backend/data/users.db", &db) ==
      SQLITE_OK) {
    const char *sql = R"(
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                lastseen TEXT
            );
        )";
    char *err = nullptr;
    sqlite3_exec(db, sql, nullptr, nullptr, &err);
    if (err) {
      std::cerr << "sqlite error: " << err << "\n";
      sqlite3_free(err);
    }
  }
  if (db)
    sqlite3_close(db);

  sqlite3 *db2 = nullptr;
  if (sqlite3_open("/home/tahmid/LocalChat/backend/data/holder.db", &db2) ==
      SQLITE_OK) {
    const char *sql2 = R"(
            CREATE TABLE IF NOT EXISTS users (
                sender_id TEXT,
                reciver_id TEXT,
                message TEXT
            );
        )";
    char *err = nullptr;
    sqlite3_exec(db2, sql2, nullptr, nullptr, &err);
    if (err) {
      std::cerr << "sqlite holder error: " << err << "\n";
      sqlite3_free(err);
    }
  }
  if (db2)
    sqlite3_close(db2);
}

// ---------------------- Client handler ----------------------
void handle_client(int connfd, sockaddr_in addr) {
  char addrbuf[INET_ADDRSTRLEN];
  inet_ntop(AF_INET, &addr.sin_addr, addrbuf, sizeof(addrbuf));
  int port = ntohs(addr.sin_port);
  std::cout << "Connected by " << addrbuf << ":" << port << "\n";

  // open DBs per-thread
  sqlite3 *db = nullptr;
  sqlite3_open("/home/tahmid/LocalChat/backend/data/users.db", &db);
  sqlite3 *holder_db = nullptr;
  sqlite3_open("/home/tahmid/LocalChat/backend/data/holder.db", &holder_db);

  while (running) {
    auto opt = recv_json_msg(connfd);
    if (!opt.has_value())
      break;
    std::string raw = *opt;
    if (raw.empty())
      continue;

    // parse
    std::unordered_map<std::string, std::string> msg;
    try {
      msg = parse_json_object(raw);
    } catch (const std::exception &e) {
      std::cerr << "JSON parse error: " << e.what() << " raw=" << raw << "\n";
      break;
    }

    auto type_it = msg.find("type");
    if (type_it == msg.end()) {
      std::cerr << "no type\n";
      break;
    }
    std::string type = type_it->second;
    std::cout << "[FROM " << addrbuf << ":" << port << "] " << raw << "\n";

    if (type == "create_user") {
      std::string name = msg.count("name") ? msg["name"] : "";
      std::string now = std::to_string((long long)time(nullptr));

      const char *insert_sql =
          "INSERT INTO users (name, lastseen) VALUES (?, ?);";
      sqlite3_stmt *stmt = nullptr;
      if (sqlite3_prepare_v2(db, insert_sql, -1, &stmt, nullptr) == SQLITE_OK) {
        sqlite3_bind_text(stmt, 1, name.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_text(stmt, 2, now.c_str(), -1, SQLITE_TRANSIENT);
        if (sqlite3_step(stmt) != SQLITE_DONE) {
          std::cerr << "insert failed\n";
        }
      } else {
        std::cerr << "prepare failed create_user\n";
      }
      sqlite3_finalize(stmt);

      int user_id = (int)sqlite3_last_insert_rowid(db);
      {
        std::lock_guard<std::mutex> lk(clients_mtx);
        clients[user_id] = connfd;
      }
      std::string resp = build_json_object(
          {{"type", "user_id"}, {"id", std::to_string(user_id)}});
      send_json_msg(connfd, resp);

    } else if (type == "ping") {
      int id = 0;
      try {
        id = std::stoi(msg.count("id") ? msg["id"] : "0");
      } catch (...) {
        id = 0;
      }
      std::string now = std::to_string((long long)time(nullptr));
      const char *update_sql = "UPDATE users SET lastseen = ? WHERE id = ?;";
      sqlite3_stmt *up = nullptr;
      if (sqlite3_prepare_v2(db, update_sql, -1, &up, nullptr) == SQLITE_OK) {
        sqlite3_bind_text(up, 1, now.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_int(up, 2, id);
        sqlite3_step(up);
      }
      sqlite3_finalize(up);

      {
        std::lock_guard<std::mutex> lk(clients_mtx);
        clients[id] = connfd;
      }

      // fetch pending messages for reciver_id == id in holder_db
      const char *sel =
          "SELECT sender_id, message FROM users WHERE reciver_id = ?;";
      sqlite3_stmt *sel_st = nullptr;
      if (sqlite3_prepare_v2(holder_db, sel, -1, &sel_st, nullptr) ==
          SQLITE_OK) {
        sqlite3_bind_int(sel_st, 1, id);
        std::vector<std::pair<std::string, std::string>> pending;
        while (sqlite3_step(sel_st) == SQLITE_ROW) {
          const unsigned char *s = sqlite3_column_text(sel_st, 0);
          const unsigned char *m = sqlite3_column_text(sel_st, 1);
          pending.emplace_back(s ? reinterpret_cast<const char *>(s) : "",
                               m ? reinterpret_cast<const char *>(m) : "");
        }
        sqlite3_finalize(sel_st);

        if (!pending.empty()) {
          std::cerr << "[" << Colors::GREEN << "DEBUG" << Colors::RESET
                    << "] FOUND PENDING MESSAGES\n";
          for (auto &p : pending) {
            std::string out = build_json_object({{"type", "message"},
                                                 {"from", p.first},
                                                 {"message", p.second}});
            send_json_msg(connfd, out);
          }
          // delete them
          const char *del = "DELETE FROM users WHERE reciver_id = ?;";
          sqlite3_stmt *del_st = nullptr;
          if (sqlite3_prepare_v2(holder_db, del, -1, &del_st, nullptr) ==
              SQLITE_OK) {
            sqlite3_bind_int(del_st, 1, id);
            sqlite3_step(del_st);
          }
          sqlite3_finalize(del_st);
          sqlite3_exec(holder_db, "COMMIT;", nullptr, nullptr, nullptr);
          std::cerr << "[" << Colors::GREEN << "DEBUG" << Colors::RESET
                    << "] REMOVED EXCESS DATA\n";
        }
      } else {
        std::cerr << "prepare failed for pending select\n";
      }

    } else if (type == "message") {
      std::string sender = msg.count("sender") ? msg["sender"] : "";
      std::string reciver = msg.count("reciver") ? msg["reciver"] : "";
      std::string message = msg.count("message") ? msg["message"] : "";

      std::cerr << "[" << Colors::GREEN << "DEBUG" << Colors::RESET
                << "] Msg from " << sender << " to " << reciver << ": "
                << message << "\n";

      int rid = 0;
      try {
        rid = std::stoi(reciver);
      } catch (...) {
        rid = 0;
      }

      bool delivered = false;
      {
        std::lock_guard<std::mutex> lk(clients_mtx);
        auto it = clients.find(rid);
        if (it != clients.end()) {
          int target_fd = it->second;
          std::string out = build_json_object(
              {{"type", "message"}, {"from", sender}, {"message", message}});
          if (send_json_msg(target_fd, out)) {
            delivered = true;
          } else {
            // failed to send; we'll store
            delivered = false;
          }
        }
      }
      if (!delivered) {
        const char *ins = "INSERT INTO users (sender_id, reciver_id, message) "
                          "VALUES (?, ?, ?);";
        sqlite3_stmt *ins_st = nullptr;
        if (sqlite3_prepare_v2(holder_db, ins, -1, &ins_st, nullptr) ==
            SQLITE_OK) {
          sqlite3_bind_text(ins_st, 1, sender.c_str(), -1, SQLITE_TRANSIENT);
          sqlite3_bind_text(ins_st, 2, reciver.c_str(), -1, SQLITE_TRANSIENT);
          sqlite3_bind_text(ins_st, 3, message.c_str(), -1, SQLITE_TRANSIENT);
          sqlite3_step(ins_st);
        }
        sqlite3_finalize(ins_st);
        sqlite3_exec(holder_db, "COMMIT;", nullptr, nullptr, nullptr);
      }

    } else if (type == "contact") {
      const char *q = "SELECT name, id FROM users;";
      sqlite3_stmt *st = nullptr;
      std::vector<std::pair<std::string, std::string>> list;
      if (sqlite3_prepare_v2(db, q, -1, &st, nullptr) == SQLITE_OK) {
        while (sqlite3_step(st) == SQLITE_ROW) {
          const unsigned char *name = sqlite3_column_text(st, 0);
          int uid = sqlite3_column_int(st, 1);
          list.emplace_back(name ? reinterpret_cast<const char *>(name) : "",
                            std::to_string(uid));
        }
      }
      sqlite3_finalize(st);

      // build JSON: {"type":"usernames","usernames":[["name",id], ...]}
      // We'll build a simple array of arrays.
      std::ostringstream oss;
      oss << '{';
      oss << "\"type\":\"usernames\",";
      oss << "\"usernames\":[";
      bool first = true;
      for (auto &p : list) {
        if (!first)
          oss << ',';
        first = false;
        oss << '[' << '"' << json_escape(p.first) << '"' << ',' << '"'
            << json_escape(p.second) << '"' << ']';
      }
      oss << "]}";
      send_json_msg(connfd, oss.str());

    } else {
      // unknown: echo ack
      std::string ack = "ACK";
      send_all(connfd, ack.c_str(), ack.size()); // note: fallback
    }
  }

  // cleanup DBs
  if (db)
    sqlite3_close(db);
  if (holder_db)
    sqlite3_close(holder_db);

  // remove mapping
  {
    std::lock_guard<std::mutex> lk(clients_mtx);
    for (auto it = clients.begin(); it != clients.end(); ++it) {
      if (it->second == connfd) {
        clients.erase(it);
        break;
      }
    }
  }

  close(connfd);
  std::cout << "Disconnected " << addrbuf << ":" << port << "\n";
}

// small helper wrapper for send_all used above in unknown branch
ssize_t send_all(int fd, const void *buf, size_t count) {
  return write_all(fd, buf, count);
}

// ---------------------- main ----------------------
int main() {
  signal(SIGPIPE, SIG_IGN);
  initialize();

  int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
  if (listen_fd < 0) {
    std::cerr << "socket() failed: " << strerror(errno) << "\n";
    return 1;
  }

  int opt = 1;
  setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

  sockaddr_in srv{};
  srv.sin_family = AF_INET;
  srv.sin_addr.s_addr = INADDR_ANY;
  srv.sin_port = htons(12345);

  if (bind(listen_fd, (sockaddr *)&srv, sizeof(srv)) < 0) {
    std::cerr << "bind() failed: " << strerror(errno) << "\n";
    close(listen_fd);
    return 1;
  }

  if (listen(listen_fd, 128) < 0) {
    std::cerr << "listen() failed: " << strerror(errno) << "\n";
    close(listen_fd);
    return 1;
  }

  std::cout << "[" << Colors::RED << "RUNNING" << Colors::RESET
            << "] Server listening on 0.0.0.0:12345\n";

  while (running) {
    sockaddr_in cli{};
    socklen_t len = sizeof(cli);
    int conn = accept(listen_fd, (sockaddr *)&cli, &len);
    if (conn < 0) {
      if (errno == EINTR)
        continue;
      std::cerr << "accept() failed: " << strerror(errno) << "\n";
      break;
    }
    std::thread t(handle_client, conn, cli);
    t.detach();
  }

  close(listen_fd);
  return 0;
}
