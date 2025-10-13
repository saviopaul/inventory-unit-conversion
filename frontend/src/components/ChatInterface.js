import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

function ChatInterface({ apiUrl, onClose, onReportGenerated }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm your AI Report Assistant. I can help you build custom reports. Try asking:\n\n• 'Create a DSR report'\n• 'Show me stock data'\n• 'I need sales report with items and quantities'"
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: messages
        })
      });

      const data = await response.json();

      // Add assistant response
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.message,
          suggestions: data.suggested_columns || [],
          action: data.action
        }
      ]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.'
        }
      ]);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-title">
          <span className="chat-icon">🤖</span>
          <h3>AI Report Assistant</h3>
        </div>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{msg.content}</div>
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="suggestions">
                  <p className="suggestions-title">Suggested columns:</p>
                  {msg.suggestions.map((sug, sidx) => (
                    <div key={sidx} className="suggestion-item">
                      <span className="sug-column">{sug.column}</span>
                      <span className="sug-report">Report {sug.report_id}</span>
                      <span className="sug-reason">{sug.reason}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me to build a report..."
          rows="3"
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          {loading ? '...' : '➤'}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;