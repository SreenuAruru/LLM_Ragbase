import React from "react";
import { Box, Typography, Divider } from "@mui/material";

const ChatHistory = ({ messages }) => (
  <Box>
    {messages.map((msg, index) => (
      <Box key={index} mb={2}>
        <Typography color={msg.role === "user" ? "primary" : "textSecondary"}>
          {msg.role === "user" ? "You" : "Assistant"}: {msg.content}
        </Typography>
        <Divider />
      </Box>
    ))}
  </Box>
);

export default ChatHistory;
