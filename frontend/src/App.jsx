import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("Searching the reports...");

  const suggestions = [
    {
      icon: "01",
      title: "Accident trends",
      text: "How did fatal accidents change from 2013 to 2022?",
    },
    {
      icon: "02",
      title: "Coal mines",
      text: "Tell me about coal mine accidents in 2016.",
    },
    {
      icon: "03",
      title: "Major causes",
      text: "What were the major causes of serious accidents?",
    },
    {
      icon: "04",
      title: "Non-coal mines",
      text: "What was the number of fatal accidents in 2013 in non-coal mines?",
    },
  ];

  const renderMessage = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);

    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={index}>
            {part.slice(2, -2)}
          </strong>
        );
      }

      return part;
    });
  };

  const askQuestion = async (questionText = question) => {
    if (!questionText.trim() || loading) return;

    const userQuestion = questionText.trim();

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: userQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);
    setLoadingText("Searching the reports...");

    // Give the user some feedback while the backend is working.
    const loadingTimer = setTimeout(() => {
      setLoadingText("Analyzing the relevant pages...");
    }, 4000);

    const timeoutController = new AbortController();

    // Maximum frontend wait time: 60 seconds.
    const timeoutTimer = setTimeout(() => {
      timeoutController.abort();
    }, 60000);

    try {
      const response = await fetch(
  "http://127.0.0.1:8000/ask",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: userQuestion,
    }),
    signal: timeoutController.signal,
  }
);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Something went wrong"
        );
      }

      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          text: data.answer,
        },
      ]);
    } catch (error) {
      if (error.name === "AbortError") {
        setMessages((prev) => [
          ...prev,
          {
            type: "error",
            text:
              "The request took longer than expected. Please try the question again.",
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            type: "error",
            text:
              "Unable to connect to the SANKET backend. Please make sure the FastAPI server is running.",
          },
        ]);
      }
    } finally {
      clearTimeout(loadingTimer);
      clearTimeout(timeoutTimer);
      setLoading(false);
      setLoadingText("Searching the reports...");
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      askQuestion();
    }
  };

  const newChat = () => {
    setMessages([]);
    setQuestion("");
  };

  useEffect(() => {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <div className="app">

      {/* Background decoration */}
      <div className="background-orb orb-one"></div>
      <div className="background-orb orb-two"></div>

      {/* NAVBAR */}
      <header className="navbar">

        <div className="brand">

          <div className="logo-mark">
            S
          </div>

          <div className="brand-text">
            <div className="brand-name">
              SANKET
            </div>

            <div className="brand-subtitle">
              Statistical Analysis & Numbers
            </div>
          </div>

        </div>

        <div className="nav-actions">

          <div className="status-pill">
            <span className="status-dot"></span>
            Documents ready
          </div>

          {messages.length > 0 && (
            <button
              className="new-chat-button"
              onClick={newChat}
            >
              <span>+</span>
              New chat
            </button>
          )}

        </div>

      </header>

      {/* MAIN */}
      <main className="main">

        {messages.length === 0 ? (

          <section className="home">

            <div className="eyebrow">
              <span className="eyebrow-dot"></span>
              DOCUMENT INTELLIGENCE
            </div>

            <h1>
              Ask questions.
              <br />
              <span>Find answers.</span>
            </h1>

            <p className="hero-description">
              Explore insights from the SANKET mining accident
              reports using natural language.
            </p>

            {/* MAIN SEARCH */}
            <div className="hero-search-wrapper">

              <div className="search-box">

                <textarea
                  value={question}
                  onChange={(event) =>
                    setQuestion(event.target.value)
                  }
                  onKeyDown={handleKeyDown}
                  placeholder="Ask something about the mining reports..."
                  rows={1}
                />

                <button
                  className="search-button"
                  onClick={() => askQuestion()}
                  disabled={
                    loading ||
                    !question.trim()
                  }
                >
                  <span>↑</span>
                </button>

              </div>

              <div className="search-footer">
                <span>
                  Enter to ask
                </span>

                <span>
                  Answers grounded in your documents
                </span>
              </div>

            </div>

            {/* SUGGESTIONS */}
            <div className="suggested-section">

              <div className="section-heading">

                <div>
                  <div className="section-eyebrow">
                    EXPLORE THE REPORTS
                  </div>

                  <div className="section-title">
                    Try a question
                  </div>
                </div>

              </div>

              <div className="suggestions">

                {suggestions.map((item, index) => (

                  <button
                    key={index}
                    className="suggestion-card"
                    onClick={() =>
                      askQuestion(item.text)
                    }
                  >

                    <div className="suggestion-top">

                      <span className="suggestion-number">
                        {item.icon}
                      </span>

                      <span className="suggestion-arrow">
                        ↗
                      </span>

                    </div>

                    <div className="suggestion-title">
                      {item.title}
                    </div>

                    <div className="suggestion-text">
                      {item.text}
                    </div>

                  </button>

                ))}

              </div>

            </div>

            <div className="home-footer">
              <span className="footer-line"></span>
              Powered by retrieval-augmented generation
              <span className="footer-line"></span>
            </div>

          </section>

        ) : (

          <section className="conversation">

            <div className="conversation-header">

              <div>
                <div className="conversation-label">
                  SANKET CHAT
                </div>

                <h2>
                  Mining report analysis
                </h2>
              </div>

              <div className="conversation-status">
                <span></span>
                Document grounded
              </div>

            </div>

            {messages.map((message, index) => (

              <div
                key={index}
                className={`message-row ${message.type}`}
              >

                {message.type !== "user" && (
                  <div className="assistant-avatar">
                    S
                  </div>
                )}

                <div className="message-container">

                  <div className="message-author">
                    {message.type === "user"
                      ? "You"
                      : message.type === "error"
                      ? "SANKET"
                      : "SANKET Assistant"}
                  </div>

                  <div className="message-bubble">

                    {message.type === "error" && (
                      <div className="error-icon">
                        !
                      </div>
                    )}

                    <div className="message-text">
                      {renderMessage(message.text)}
                    </div>

                  </div>

                </div>

              </div>

            ))}

            {loading && (

              <div className="message-row assistant">

                <div className="assistant-avatar">
                  S
                </div>

                <div className="message-container">

                  <div className="message-author">
                    SANKET Assistant
                  </div>

                  <div className="loading-bubble">

                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>

                    <span>
                      {loadingText}
                    </span>

                  </div>

                </div>

              </div>

            )}

          </section>

        )}

      </main>

      {/* BOTTOM INPUT */}
      {messages.length > 0 && (

        <div className="bottom-area">

          <div className="bottom-input-wrapper">

            <div className="bottom-input">

              <textarea
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                onKeyDown={handleKeyDown}
                placeholder="Ask another question..."
                rows={1}
              />

              <button
                className="send-button"
                onClick={() => askQuestion()}
                disabled={
                  loading ||
                  !question.trim()
                }
              >
                ↑
              </button>

            </div>

            <div className="bottom-note">
              SANKET answers are generated from the provided
              documents.
            </div>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;