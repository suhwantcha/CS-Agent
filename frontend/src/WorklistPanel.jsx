import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemButton, ListItemText, Divider, CircularProgress, Alert } from '@mui/material';
import axios from 'axios';

const WorklistPanel = ({ onInquirySelect }) => {
  const [newInquiries, setNewInquiries] = useState([]);
  const [completedInquiries, setCompletedInquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // "내가 처리 중인 문의"는 아직 기능이 없으므로 더미 데이터 사용
  const inProgressInquiries = [
    // { id: 'q3', customer_id: 'at_risk_02', question_text: '반품 절차 문의' },
  ];

  useEffect(() => {
    const fetchInquiries = async () => {
      setLoading(true);
      setError(null);
      console.log("WorklistPanel: 문의 목록 가져오기 시작...");
      try {
        const newRes = await axios.get('http://127.0.0.1:8000/api/inquiries?status=new');
        console.log("WorklistPanel: '새로 들어온 문의' API 응답:", newRes.data);
        setNewInquiries(newRes.data.inquiries);

        const completedRes = await axios.get('http://127.0.0.1:8000/api/inquiries?status=completed');
        console.log("WorklistPanel: '처리 완료' API 응답:", completedRes.data);
        setCompletedInquiries(completedRes.data.inquiries);
        console.log("WorklistPanel: 문의 목록 가져오기 성공.");
      } catch (err) {
        setError('문의 목록을 불러오는 데 실패했습니다.');
        console.error('WorklistPanel: 문의 목록 API 호출 실패:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchInquiries();
  }, []);

  if (loading) {
    return (
      <Paper elevation={3} sx={{ p: 2, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Paper elevation={3} sx={{ p: 2, height: '100%', overflowY: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        문의 대기열
      </Typography>
      <Divider sx={{ mb: 2 }} />

      <Box>
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>새로 들어온 문의 ({newInquiries.length})</Typography>
        <List dense>
          {newInquiries.map(item => (
            <ListItemButton key={item.question_id} onClick={() => onInquirySelect(item)}>
              <ListItemText primary={item.question_text} secondary={`고객 ID: ${item.customer_id}`} />
            </ListItemButton>
          ))}
        </List>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box>
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>내가 처리 중인 문의 ({inProgressInquiries.length})</Typography>
        {inProgressInquiries.length > 0 ? (
          <List dense>
            {inProgressInquiries.map(item => (
              <ListItemButton key={item.id} onClick={() => onInquirySelect(item)}>
                <ListItemText primary={item.question_text} />
              </ListItemButton>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ml: 2}}>없음</Typography>
        )}
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box>
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>처리 완료 ({completedInquiries.length})</Typography>
        <List dense>
          {completedInquiries.map(item => (
            <ListItemButton key={item.question_id} onClick={() => onInquirySelect(item)}>
              <ListItemText primary={item.question_text} secondary={`고객 ID: ${item.customer_id}`} />
            </ListItemButton>
          ))}
        </List>
      </Box>
    </Paper>
  );
};

export default WorklistPanel;
