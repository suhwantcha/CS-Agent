import React, { useState } from 'react';
import { Box, TextField, Button, List, ListItem, ListItemText, Paper, Typography, CircularProgress, IconButton } from '@mui/material';
import { ThumbUp, ThumbDown } from '@mui/icons-material';
import axios from 'axios';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (input.trim() === '') return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('customer_query', input);
      // In a real app, you'd get the customer_id from auth.
      formData.append('customer_id', 'TEST_USER_FRONTEND'); 

      const response = await axios.post('http://127.0.0.1:8000/api/query', formData);

      const aiMessage = {
        sender: 'ai',
        text: response.data.answer,
        log_id: response.data.log_id,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        sender: 'ai',
        text: `Error: ${error.response?.data?.detail || error.message}`,
        log_id: null,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (log_id, feedback) => {
    // This is a placeholder for a more complex feedback UI
    let final_resolution = null;
    if (feedback === 'failure') {
      final_resolution = prompt('어떤 답변이 올바른 답변인가요?');
      if (final_resolution === null || final_resolution.trim() === '') {
        alert('올바른 답변을 입력해야 피드백을 보낼 수 있습니다.');
        return;
      }
    }

    try {
        const formData = new FormData();
        formData.append('log_id', log_id);
        formData.append('resolution_feedback', feedback);
        if (final_resolution) {
            formData.append('final_resolution', final_resolution);
        }
        
        await axios.post('http://127.0.0.1:8000/api/feedback', formData);
        alert('피드백이 성공적으로 전송되었습니다!');
    } catch (error) {
        alert(`피드백 전송 실패: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <Paper elevation={3} sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
        <List>
          {messages.map((msg, index) => (
            <ListItem key={index} sx={{ justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              <Box
                sx={{
                  bgcolor: msg.sender === 'user' ? 'primary.main' : 'grey.300',
                  color: msg.sender === 'user' ? 'primary.contrastText' : 'text.primary',
                  p: 1.5,
                  borderRadius: 2,
                  maxWidth: '70%',
                }}
              >
                <ListItemText primary={msg.text} />
                {msg.sender === 'ai' && msg.log_id && (
                  <Box sx={{ mt: 1 }}>
                    <IconButton size="small" onClick={() => handleFeedback(msg.log_id, 'success')}>
                      <ThumbUp fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleFeedback(msg.log_id, 'failure')}>
                      <ThumbDown fontSize="small" />
                    </IconButton>
                  </Box>
                )}
              </Box>
            </ListItem>
          ))}
        </List>
      </Box>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
          disabled={loading}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleSend}
          disabled={loading}
          sx={{ ml: 1, p: "14px" }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : '전송'}
        </Button>
      </Box>
    </Paper>
  );
};

export default Chat;
