import React from 'react';
import { Box, Typography } from '@mui/material';
import Chat from './Chat'; // 기존 Chat 컴포넌트 임포트

const CSAgentHub = () => {
  return (
    <Box sx={{ mt: 4, p: 3, border: '1px dashed grey' }}>
      <Typography variant="h5" component="h2" gutterBottom>
        상담원용 CS 대화 허브 (응대 모드)
      </Typography>
      <Typography variant="body1" sx={{ mb: 2 }}>
        여기에 상담원용 UI 컴포넌트들이 들어갑니다. (현재는 채팅 컴포넌트만)
      </Typography>
      <Chat /> {/* 기존 채팅 컴포넌트를 상담원 허브 내에 렌더링 */}
    </Box>
  );
};

export default CSAgentHub;