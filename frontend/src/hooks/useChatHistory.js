import { useState, useCallback } from 'react';

// Hook Customizado para gerenciar o histórico de mensagens
export const useChatHistory = () => {
  const initialMessages = [
    { id: "0", text: "Olá! Eu sou o ChatBot UERN. Pergunte sobre o calendário acadêmico, reitoria ou disciplinas de maior dificuldade.", sender: "bot" }
  ];
  
  const [messages, setMessages] = useState(initialMessages);

  // Função para adicionar uma nova mensagem
  const addMessage = useCallback((text, sender) => {
    const newMessage = {
      id: Date.now().toString(),
      text,
      sender,
    };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
  }, []);

  // Função para limpar o histórico (usado no botão "Logout" do chat)
  const clearHistory = useCallback(() => {
    setMessages(initialMessages);
  }, []);

  return { messages, addMessage, clearHistory };
};