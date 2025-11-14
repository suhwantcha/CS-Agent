import React, { useState } from 'react';
import { Box, Typography, Grid } from '@mui/material';
import Chat from './Chat';
import CustomerInfoPanel from './CustomerInfoPanel';
import WorklistPanel from './WorklistPanel'; // 새로 만든 문의 대기열 패널 임포트

const CSAgentHub = () => {
  const [selectedInquiry, setSelectedInquiry] = useState(null);

  console.log("CSAgentHub.jsx: 컴포넌트 렌더링됨.");

  const handleInquirySelect = (inquiry) => {
    setSelectedInquiry(inquiry);
  };

  return (
    <Box sx={{ mt: 2, flexGrow: 1 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        상담원용 CS 대화 허브 (응대 모드)
      </Typography>
      
      <Grid container spacing={2} sx={{ mt: 1, height: 'calc(85vh)' }}>
        {/* 왼쪽 열: 문의 대기열 */}
        <Grid item xs={12} md={3}>
          <WorklistPanel onInquirySelect={handleInquirySelect} />
        </Grid>

        {/* 가운데 열: 채팅 패널 */}
        <Grid item xs={12} md={5}>
          <Chat 
            key={selectedInquiry ? selectedInquiry.question_id : 'initial'}
            inquiry={selectedInquiry} 
          />
        </Grid>

        {/* 오른쪽 열: 고객 정보 패널 */}
        <Grid item xs={12} md={4}>
          <CustomerInfoPanel 
            customerId={selectedInquiry ? selectedInquiry.customer_id : null} 
            inquiry={selectedInquiry}
          />
        </Grid>

        {/* 오른쪽 열: 고객 정보 패널 (임시 주석 처리) */}
        {/*
        <Grid item xs={12} md={4}>
          <CustomerInfoPanel 
            customerId={selectedInquiry ? selectedInquiry.customer_id : null} 
            inquiry={selectedInquiry}
          />
        </Grid>
        */}
      </Grid>
    </Box>
  );
};

export default CSAgentHub;