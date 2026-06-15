"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, User, Loader2 } from "lucide-react";

export default function Page() {
  const [messages, setMessages] = useState<{role: string, content: string}[]>([
    { role: "assistant", content: "Hello! I am the WarRoom AI Agent. I have access to Splunk, Jira, and other integrated tools. How can I assist with your investigation today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, room_id: "test_web_chat" }),
      });

      if (!response.ok) throw new Error("API Error");
      
      const data = await response.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.response }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: "assistant", content: "Error: Could not reach the WarRoom Agent backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto border rounded-xl overflow-hidden bg-background">
      <div className="flex items-center px-6 py-4 border-b bg-muted/30">
        <Bot className="w-6 h-6 mr-3 text-primary" />
        <div>
          <h2 className="text-lg font-semibold">WarRoom Agent Testing</h2>
          <p className="text-sm text-muted-foreground">This simulates the Slack interface. Tools are active.</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`flex max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
              <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${msg.role === "user" ? "bg-primary ml-3" : "bg-muted border mr-3"}`}>
                {msg.role === "user" ? <User className="h-4 w-4 text-primary-foreground" /> : <Bot className="h-4 w-4" />}
              </div>
              <div className={`px-4 py-3 rounded-2xl text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted/50 border"}`}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex flex-row max-w-[80%]">
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-muted border mr-3 flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <div className="px-4 py-3 rounded-2xl text-sm bg-muted/50 border flex items-center">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Agent is thinking and calling tools...
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t bg-muted/10">
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex items-center space-x-2">
          <Input 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="E.g., @WarRoom check SEC-123 or query Splunk for failed logins..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="h-4 w-4 mr-2" />
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
