import React from "react";
import { Box, CircularProgress, Typography } from "@mui/material";

const LoadingOverlay = ({ message }) => (
  <Box
    position="fixed"
    top={0}
    left={0}
    right={0}
    bottom={0}
    display="flex"
    justifyContent="center"
    alignItems="center"
    bgcolor="rgba(0, 0, 0, 0.7)"
    zIndex={9999}
  >
    <CircularProgress color="primary" />
    <Typography variant="h6" color="primary" ml={2}>
      {message}
    </Typography>
  </Box>
);

export default LoadingOverlay;
