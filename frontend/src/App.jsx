import React, { useState } from 'react';
import { Container, Typography, Box, Button, ButtonGroup } from '@mui/material';
import AdminDashboard from './AdminDashboard'; // AdminDashboard 컴포넌트 임포트
import CSAgentHub from './CSAgentHub';     // CSAgentHub 컴포넌트 임포트

function App() {
  const [userRole, setUserRole] = useState(null); // 'admin', 'agent', or null

  const handleRoleSelect = (role) => {
    console.log(`App.jsx: 역할 선택됨 -> ${role}`);
    setUserRole(role);
  };

  console.log(`App.jsx: 현재 렌더링 중. userRole: ${userRole}`);

  return (
    <Container maxWidth="lg"> {/* maxWidth를 lg로 확장하여 대시보드 공간 확보 */}
      <Box sx={{ my: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          SmartCRM
        </Typography>
        <Typography variant="h6" component="h2" gutterBottom sx={{ mt: -2, mb: 3, color: 'text.secondary' }}>
          AI Customer Manager for Self-Employed Owners
        </Typography>

        {!userRole ? (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h5" component="h2" gutterBottom>
              역할을 선택해주세요
            </Typography>
            <ButtonGroup variant="contained" aria-label="Role selection buttons">
              <Button onClick={() => handleRoleSelect('admin')}>관리자/CEO</Button>
              <Button onClick={() => handleRoleSelect('agent')}>상담원</Button>
            </ButtonGroup>
          </Box>
        ) : (
          <>
            <Button 
              variant="outlined" 
              onClick={() => setUserRole(null)} 
              sx={{ mb: 2 }}
            >
              뒤로가기
            </Button>
            {userRole === 'admin' ? (
              <AdminDashboard />
            ) : (
              <CSAgentHub />
            )}
          </>
        )}
      </Box>
    </Container>
  );
}

export default App;