import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#ff9800", // Orange buttons/text
    },
    background: {
      default: "#191a1f", // Dark theme background
    },
  },
});

export default theme;
