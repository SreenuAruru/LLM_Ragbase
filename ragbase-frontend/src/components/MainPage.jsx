import React, { useState, useEffect } from "react";
import { Box, Typography, TextField, Button, Avatar } from "@mui/material";
import axios from "axios";
import askQuestionIcon from "../assets/ask question.webp";
import aiResponseIcon from "../assets/ai response icon.jpg";
import LoadingOverlay from "./LoadingOverlay";

const MainPage = () => {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get(
        "http://localhost:8000/conversation_history/"
      );
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error("Failed to fetch conversation history:", error);
    }
  };

  const handleAskQuestion = async () => {
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/ask_question/", {
        question,
      });
      setMessages((prev) => [
        ...prev,
        { role: "user", content: question },
        { role: "assistant", content: response.data.response },
      ]);
    } catch (error) {
      console.error("Failed to ask question:", error);
    } finally {
      setLoading(false);
      setQuestion("");
    }
  };

  useEffect(() => {
    fetchChatHistory();
  }, []);

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#1e1e1e",
        color: "#fff",
        fontFamily: "Roboto, sans-serif",
      }}
    >
      {/* Show LoadingOverlay when loading */}
      {loading && <LoadingOverlay message="Fetching response..." />}

      {/* Chat History */}
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          padding: 2,
          "&::-webkit-scrollbar": {
            width: "8px",
          },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: "#555",
            borderRadius: "4px",
          },
        }}
      >
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: "flex",
              alignItems: "flex-start",
              marginBottom: 2,
            }}
          >
            <Avatar
              src={message.role === "user" ? askQuestionIcon : aiResponseIcon}
              alt={message.role}
              sx={{
                width: 40,
                height: 40,
                marginRight: 2,
                backgroundColor: "#444",
              }}
            />
            <Box
              sx={{
                backgroundColor:
                  message.role === "user" ? "transparent" : "#333",
                padding: 2,
                borderRadius: "8px",
                maxWidth: "80%",
              }}
            >
              <Typography
                variant="body1"
                sx={{
                  fontSize: "14px",
                  lineHeight: "20px",
                  wordWrap: "break-word",
                }}
              >
                {message.content}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>

      {/* Input Section Fixed to Bottom */}
      <Box
        sx={{
          position: "sticky",
          bottom: 0,
          left: 0,
          width: "100%",
          display: "flex",
          alignItems: "center",
          backgroundColor: "#1e1e1e",
          padding: 2,
          borderTop: "1px solid #444",
        }}
      >
        <TextField
          variant="outlined"
          placeholder="Ask your question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          fullWidth
          disabled={loading}
          sx={{
            marginRight: 2,
            backgroundColor: "#2c2c2c",
            borderRadius: "4px",
            input: { color: "#fff" },
          }}
        />
        <Button
          variant="contained"
          sx={{
            backgroundColor: "#ff9800",
            color: "#fff",
            fontWeight: "bold",
            padding: "8px 16px",
            "&:hover": { backgroundColor: "#e68a00" },
          }}
          onClick={handleAskQuestion}
          disabled={loading || !question}
        >
          Ask
        </Button>
      </Box>
    </Box>
  );
};

export default MainPage;
