import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import Chat from './Chat';

function App() {
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4, textAlign: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          AI CS Agent
        </Typography>
        <Chat />
      </Box>
    </Container>
  );
}

export default App;