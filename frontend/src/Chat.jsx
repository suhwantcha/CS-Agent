import React, { useState, useEffect } from 'react';
import { Box, TextField, Button, List, ListItem, ListItemText, Paper, Typography, CircularProgress, IconButton } from '@mui/material';
import { ThumbUp, ThumbDown } from '@mui/icons-material';
import axios from 'axios';

const Chat = ({ inquiry }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState('');
  const [suggestionLoading, setSuggestionLoading] = useState(false);

  // inquiry prop이 변경될 때마다 (새 문의가 선택될 때마다) 실행
  useEffect(() => {
    if (!inquiry) {
      setMessages([]);
      setInput('');
      setAiSuggestion('');
      return;
    }

    // 새 문의가 선택되면 기존 채팅 내용 초기화
    setMessages([{ sender: 'user', text: inquiry.question_text }]);
    setInput('');
    setAiSuggestion('');
    setSuggestionLoading(true);

    const fetchSuggestion = async () => {
      try {
        const response = await axios.get(`http://127.0.0.1:8000/api/ai/suggestion?query=${encodeURIComponent(inquiry.question_text)}`);
        setAiSuggestion(response.data.suggestion);
      } catch (error) {
        console.error('Failed to fetch AI suggestion:', error);
        setAiSuggestion('AI 답변 제안을 가져오는 데 실패했습니다.');
      } finally {
        setSuggestionLoading(false);
      }
    };

    fetchSuggestion();

  }, [inquiry]);


  const handleSend = async () => {
    if (input.trim() === '' || !inquiry) return;

    const userMessage = { sender: 'agent', text: input }; // 상담원이 보내는 메시지
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const payload = {
        customer_id: inquiry.customer_id,
        query: input, // 상담원이 직접 입력한 내용으로 쿼리
      };

      const response = await axios.post('http://127.0.0.1:8000/api/chat', payload);

      const aiMessage = {
        sender: 'ai',
        text: response.data.response,
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

  if (!inquiry) {
    return (
        <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="h6" color="text.secondary">
                왼쪽에서 문의를 선택해주세요.
            </Typography>
        </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
        <List>
          {messages.map((msg, index) => (
            <ListItem key={index} sx={{ justifyContent: msg.sender === 'user' || msg.sender === 'agent' ? 'flex-end' : 'flex-start' }}>
              <Box
                sx={{
                  bgcolor: msg.sender === 'user' || msg.sender === 'agent' ? 'primary.main' : 'grey.300',
                  color: msg.sender === 'user' || msg.sender === 'agent' ? 'primary.contrastText' : 'text.primary',
                  p: 1.5,
                  borderRadius: 2,
                  maxWidth: '80%',
                }}
              >
                <ListItemText 
                    primary={msg.text} 
                    secondary={msg.sender === 'user' ? '고객' : msg.sender === 'agent' ? '상담원' : 'AI'}
                    secondaryTypographyProps={{ 
                        color: msg.sender === 'user' || msg.sender === 'agent' ? 'rgba(255, 255, 255, 0.7)' : 'text.secondary',
                        textAlign: 'left'
                    }}
                />
                {msg.sender === 'ai' && msg.log_id && (
                  <Box sx={{ mt: 1, textAlign: 'right' }}>
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
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', borderTop: '1px solid #ddd' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.input)}
          onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
          disabled={loading || !inquiry}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleSend}
          disabled={loading || !inquiry}
          sx={{ ml: 1, p: "14px" }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : '전송'}
        </Button>
      </Box>

      {/* AI 답변 제안 및 도구 영역 */}
      <Paper elevation={2} sx={{ p: 2, borderTop: '1px solid #ddd' }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
          🤖 AI 답변 제안
        </Typography>
        <Box sx={{ p: 1.5, bgcolor: 'action.hover', borderRadius: 1, mb: 1, minHeight: '50px' }}>
            {suggestionLoading ? <CircularProgress size={20} /> : (
                <Typography variant="body2">
                    {aiSuggestion}
                </Typography>
            )}
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button 
            variant="outlined" 
            size="small"
            onClick={() => setInput(aiSuggestion)}
            disabled={suggestionLoading || !aiSuggestion}
          >
            ✅ AI 답변 사용
          </Button>
          <div>
            <IconButton size="small" onClick={() => alert('피드백 기능이 호출됩니다.')} disabled={suggestionLoading}>
              <ThumbDown fontSize="small" />
            </IconButton>
            <Button 
              variant="text" 
              size="small"
              onClick={() => document.getElementById('file-input').click()}
            >
              📎 첨부
            </Button>
            <input type="file" id="file-input" style={{ display: 'none' }} />
          </div>
        </Box>
      </Paper>
    </Paper>
  );
};

export default Chat;
