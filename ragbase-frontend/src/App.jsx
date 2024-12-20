import React, { useState } from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import theme from "./theme";
import UploadPage from "./components/UploadPage";
import MainPage from "./components/MainPage";

const App = () => {
  const [isUploaded, setIsUploaded] = useState(false);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {!isUploaded ? (
        <UploadPage onUploadSuccess={() => setIsUploaded(true)} />
      ) : (
        <MainPage />
      )}
    </ThemeProvider>
  );
};

export default App;
