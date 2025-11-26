import { useState, useRef, useEffect } from "react";
import {
  MessageCircle,
  LogOut,
  Home as HomeIcon,
  Settings,
  Bell,
  User,
} from "lucide-react";

import { useChatHistory } from "./hooks/useChatHistory";

export default function App() {
  // Telas
  const [screen, setScreen] = useState("welcome");

  // Login
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Chat
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // User
  const [userName, setUserName] = useState("");

  // Histórico
  const { messages, addMessage, clearHistory } = useChatHistory();

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef?.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // -------------------------------------------------------------------
  // LOGIN
  const handleLogin = (e) => {
    e.preventDefault();

    if (email && password) {
      const username = email.split("@")[0];
      setUserName(username);
      setScreen("chat");

      setEmail("");
      setPassword("");
    }
  };

  // VISITANTE
  const handleVisitorLogin = () => {
    setUserName("Visitante");
    setScreen("chat");
  };

  // LOGOUT
  const handleLogout = () => {
    clearHistory();
    setUserName("");
    setInputValue("");
    setScreen("welcome");
  };

  // -------------------------------------------------------------------
  // ENVIAR MENSAGEM AO BACKEND
  const handleSendMessage = async () => {
    if (!inputValue.trim() || !userName) return;

    const userMessage = inputValue.trim();
    addMessage(userMessage, "user");
    setInputValue("");
    setIsLoading(true);

    try {
      const requestData = {
        session_id: userName,
        message: userMessage,
      };

      const response = await fetch("http://127.0.0.1:8000/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) throw new Error("Erro no servidor");

      const data = await response.json();
      addMessage(data.response, "bot");
    } catch (error) {
      console.error(error);
      addMessage("❌ Erro ao conectar ao servidor.", "bot");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleSendMessage();
  };

  // -------------------------------------------------------------------
  // TELAS (WELCOME, LOGIN, CHAT)

  // WELCOME
  if (screen === "welcome") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex justify-center mb-6">
              <div className="bg-accent p-3 rounded-full">
                <MessageCircle className="w-8 h-8 text-white" />
              </div>
            </div>

            <h1 className="text-3xl font-bold text-center text-foreground mb-2">
              ChatBot UERN
            </h1>

            <p className="text-center text-muted-foreground mb-2">
              Bem-vindo! Escolha como deseja continuar.
            </p>

            <div className="space-y-3">
              <button
                onClick={() => setScreen("login")}
                className="button-primary"
              >
                Fazer Login
              </button>

              <button
                onClick={handleVisitorLogin}
                className="button-secondary"
              >
                Entrar como Visitante
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // LOGIN
  if (screen === "login") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <button
              onClick={() => setScreen("welcome")}
              className="mb-6 text-muted-foreground hover:text-foreground"
            >
              ← Voltar
            </button>

            <div className="flex justify-center mb-6">
              <div className="bg-accent p-3 rounded-full">
                <MessageCircle className="w-8 h-8 text-white" />
              </div>
            </div>

            <h1 className="text-2xl font-bold text-center mb-2">Login</h1>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Email</label>
                <input
                  type="email"
                  placeholder="seu.email@uern.br"
                  className="input-field w-full mt-1"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-sm font-medium">Senha</label>
                <input
                  type="password"
                  placeholder="Senha"
                  className="input-field w-full mt-1"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <button type="submit" className="button-primary w-full">
                Entrar
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------
  // CHAT
  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <div className="w-16 bg-primary flex flex-col items-center py-4 gap-4 shadow-lg">
        <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
          <MessageCircle className="w-6 h-6 text-primary" />
        </div>

        <div className="flex-1 flex flex-col gap-4 items-center">
          <button className="sidebar-icon sidebar-icon-active">
            <MessageCircle className="w-5 h-5" />
          </button>
          <button className="sidebar-icon sidebar-icon-inactive">
            <HomeIcon className="w-5 h-5" />
          </button>
          <button className="sidebar-icon sidebar-icon-inactive">
            <Bell className="w-5 h-5" />
          </button>
          <button className="sidebar-icon sidebar-icon-inactive">
            <Settings className="w-5 h-5" />
          </button>
        </div>

        <button
          onClick={handleLogout}
          className="sidebar-icon sidebar-icon-inactive hover:bg-red-200 hover:text-red-700"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-border px-6 py-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">ChatBot UERN</h2>
              <p className="text-xs text-muted-foreground">Assistente Acadêmico</p>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">Olá, {userName}!</p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-message ${
                msg.sender === "user" ? "chat-message-user" : ""
              }`}
            >
              {msg.sender === "bot" && (
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                  <MessageCircle className="w-4 h-4 text-white" />
                </div>
              )}

              <div
                className={`chat-bubble ${
                  msg.sender === "user"
                    ? "chat-bubble-user"
                    : "chat-bubble-bot"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-message">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center animate-pulse">
                <MessageCircle className="w-4 h-4 text-white" />
              </div>
              <div className="chat-bubble chat-bubble-bot">Digitando...</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-border p-4">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Digite sua pergunta..."
              className="input-field flex-1"
              value={inputValue}
              disabled={isLoading}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              onClick={handleSendMessage}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              {isLoading ? "..." : "Enviar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
