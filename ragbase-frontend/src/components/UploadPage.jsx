import React, { useState } from "react";
import { Button, Typography, Box, CircularProgress } from "@mui/material";
import axios from "axios";

const UploadPage = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleFileUpload = async (event) => {
    setLoading(true);
    const files = event.target.files;
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append("files", file));

    try {
      const response = await axios.post(
        "http://localhost:8000/upload_documents/",
        formData
      );
      if (response.data.message) {
        onUploadSuccess();
      }
    } catch (error) {
      console.error("File upload failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      height="100vh"
    >
      <Typography variant="h4" gutterBottom>
        Upload Your Documents
      </Typography>
      {loading ? (
        <>
          <CircularProgress color="primary" />
          <p>Uploading Your Documents.....</p>
        </>
      ) : (
        <>
          <Button variant="contained" component="label" color="primary">
            Upload PDFs
            <input type="file" hidden multiple onChange={handleFileUpload} />
          </Button>
          <p>Please upload PDF documents to continue!</p>
        </>
      )}
    </Box>
  );
};

export default UploadPage;
