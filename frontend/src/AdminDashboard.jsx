import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, CircularProgress, Alert, List, ListItem, ListItemText, Divider, Paper, TextField, Button, Tabs, Tab } from '@mui/material';
import axios from 'axios';

const AdminDashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [salesTrend, setSalesTrend] = useState([]);
  const [negativeReviews, setNegativeReviews] = useState([]); // 추가
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // BI 챗봇 상태
  const [biChatMessages, setBiChatMessages] = useState([]);
  const [biChatInput, setBiChatInput] = useState('');
  const [biChatLoading, setBiChatLoading] = useState(false);

  // 고객 관리 상태
  const [vipCustomers, setVipCustomers] = useState([]); // 추가
  const [atRiskCustomers, setAtRiskCustomers] = useState([]); // 추가
  const [selectedCustomerTab, setSelectedCustomerTab] = useState('VIP'); // 추가

  useEffect(() => {
    const fetchData = async () => {
      try {
        const kpisResponse = await axios.get('http://127.0.0.1:8000/api/admin/kpis');
        setKpis(kpisResponse.data);

        const warningsResponse = await axios.get('http://127.0.0.1:8000/api/admin/warnings');
        setWarnings(warningsResponse.data.warnings);

        const salesTrendResponse = await axios.get('http://127.0.0.1:8000/api/admin/sales_trend');
        setSalesTrend(salesTrendResponse.data.sales_trend);

        const negativeReviewsResponse = await axios.get('http://127.0.0.1:8000/api/admin/negative_reviews'); // 추가
        setNegativeReviews(negativeReviewsResponse.data.negative_reviews); // 추가

        // 고객 세그먼트 데이터 로드
        const vipCustomersResponse = await axios.get('http://127.0.0.1:8000/api/admin/customers_by_segment?segment=VIP'); // 추가
        setVipCustomers(vipCustomersResponse.data.customers); // 추가

        const atRiskCustomersResponse = await axios.get('http://127.0.0.1:8000/api/admin/customers_by_segment?segment=이탈 위험 고객'); // 추가
        setAtRiskCustomers(atRiskCustomersResponse.data.customers); // 추가
        
      } catch (err) {
        setError('대시보드 데이터를 불러오는 데 실패했습니다.');
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleBiChatSubmit = async () => {
    if (biChatInput.trim() === '') return;

    const newUserMessage = { sender: 'user', text: biChatInput };
    setBiChatMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setBiChatInput('');
    setBiChatLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/chat', {
        customer_id: "BI_USER", // BI 챗봇을 위한 고정된 customer_id
        query: biChatInput,
      });
      const aiResponse = { sender: 'ai', text: response.data.response };
      setBiChatMessages((prevMessages) => [...prevMessages, aiResponse]);
    } catch (err) {
      console.error('BI Chatbot API 호출 오류:', err);
      setBiChatMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'ai', text: '죄송합니다. BI 챗봇 응답을 가져오는 데 실패했습니다.' },
      ]);
    } finally {
      setBiChatLoading(false);
    }
  };

  const handleApproveReply = async (reviewId, draftReply) => { // 추가
    try {
      await axios.post('http://127.0.0.1:8000/api/admin/approve_review_reply', {
        review_id: reviewId,
        approved_reply: draftReply,
      });
      alert('답변이 승인 및 게시되었습니다!');
      // 승인된 리뷰는 목록에서 제거하거나 상태를 업데이트할 수 있습니다.
      setNegativeReviews((prevReviews) => prevReviews.filter(review => review.review_id !== reviewId));
    } catch (err) {
      console.error('리뷰 답변 승인 오류:', err);
      alert('리뷰 답변 승인 중 오류가 발생했습니다.');
    }
  };

  const handleCustomerTabChange = (event, newValue) => { // 추가
    setSelectedCustomerTab(newValue);
  };

  const handleSendCouponToAtRiskCustomers = async () => { // 추가
    if (atRiskCustomers.length === 0) {
      alert('이탈 위험 고객이 없습니다.');
      return;
    }
    const customerIds = atRiskCustomers.map(c => c.customer_id);
    try {
      await axios.post('http://127.0.0.1:8000/api/admin/send_coupon', {
        customer_ids: customerIds,
        coupon_details: "15% 할인쿠폰",
      });
      alert(`${customerIds.length}명의 이탈 위험 고객에게 15% 할인쿠폰이 발송되었습니다!`);
    } catch (err) {
      console.error('쿠폰 발송 오류:', err);
      alert('쿠폰 발송 중 오류가 발생했습니다.');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 4, p: 3 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        관리자/CEO 대시보드 (BI 모드)
      </Typography>
      
      {/* 핵심 KPI (4-Grid) */}
      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid xs={12} sm={6} md={3}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                오늘의 정산액
              </Typography>
              <Typography variant="h4" component="div">
                {kpis.latest_settlement_amount ? kpis.latest_settlement_amount.toLocaleString() : 'N/A'}원
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                미답변 문의
              </Typography>
              <Typography variant="h4" component="div">
                {kpis.unanswered_qnas}건
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                처리 대기 클레임
              </Typography>
              <Typography variant="h4" component="div">
                {kpis.pending_claims}건
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                재고 위험 상품
              </Typography>
              <Typography variant="h4" component="div">
                {kpis.low_stock_products}건
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 선제적 경고 피드 */}
      <Box sx={{ mt: 5 }}>
        <Typography variant="h5" component="h3" gutterBottom>
          선제적 경고 피드 🔔
        </Typography>
        <Paper elevation={2} sx={{ p: 2 }}>
          {warnings.length > 0 ? (
            <List>
              {warnings.map((warning, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemText primary={warning} />
                  </ListItem>
                  {index < warnings.length - 1 && <Divider component="li" />}
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              현재 활성화된 경고가 없습니다.
            </Typography>
          )}
        </Paper>
      </Box>

      {/* 일간 매출 추이 그래프 */}
      <Box sx={{ mt: 5 }}>
        <Typography variant="h5" component="h3" gutterBottom>
          일간 매출 추이 📈
        </Typography>
        <Paper elevation={2} sx={{ p: 2 }}>
          {salesTrend.length > 0 ? (
            <List>
              {salesTrend.map((data, index) => (
                <ListItem key={index}>
                  <ListItemText primary={`${data.date}: ${data.amount.toLocaleString()}원`} />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              매출 추이 데이터가 없습니다.
            </Typography>
          )}
          {/* TODO: Chart.js 또는 Recharts와 같은 라이브러리를 사용하여 실제 그래프를 그릴 수 있습니다. */}
        </Paper>
      </Box>

      {/* AI 분석 (BI 챗봇) */}
      <Box sx={{ mt: 5 }}>
        <Typography variant="h5" component="h3" gutterBottom>
          AI 분석 (BI 챗봇) 🤖
        </Typography>
        <Paper elevation={2} sx={{ p: 2, height: 400, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ flexGrow: 1, overflowY: 'auto', mb: 2 }}>
            {biChatMessages.map((msg, index) => (
              <Box key={index} sx={{ 
                display: 'flex', 
                justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start', 
                mb: 1 
              }}>
                <Card 
                  variant="outlined" 
                  sx={{ 
                    p: 1, 
                    maxWidth: '70%', 
                    bgcolor: msg.sender === 'user' ? 'primary.light' : 'grey.200',
                    color: msg.sender === 'user' ? 'white' : 'black',
                    borderRadius: '10px'
                  }}
                >
                  <Typography variant="body2">{msg.text}</Typography>
                </Card>
              </Box>
            ))}
          </Box>
          <Box sx={{ display: 'flex' }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="BI 관련 질문을 입력하세요..."
              value={biChatInput}
              onChange={(e) => setBiChatInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleBiChatSubmit();
                }
              }}
              sx={{ mr: 1 }}
            />
            <Button 
              variant="contained" 
              onClick={handleBiChatSubmit} 
              disabled={biChatLoading}
            >
              {biChatLoading ? <CircularProgress size={24} /> : '전송'}
            </Button>
          </Box>
        </Paper>
      </Box>

      {/* 리뷰 관리 */}
      <Box sx={{ mt: 5 }}>
        <Typography variant="h5" component="h3" gutterBottom>
          리뷰 관리 📝
        </Typography>
        <Paper elevation={2} sx={{ p: 2 }}>
          {negativeReviews.length > 0 ? (
            <List>
              {negativeReviews.map((review) => (
                <Card key={review.review_id} variant="outlined" sx={{ mb: 2, p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle1">
                      {review.rating <= 2 && <span style={{ color: 'red', fontWeight: 'bold' }}>🚨긴급 </span>}
                      상품: {review.product_name} (평점: {review.rating}점)
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(review.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    리뷰 내용: {review.review_text}
                  </Typography>
                  <Typography variant="body2" color="primary.main" sx={{ mb: 2 }}>
                    AI 제안 답변: {review.draft_reply}
                  </Typography>
                  <Button 
                    variant="contained" 
                    color="success" 
                    onClick={() => handleApproveReply(review.review_id, review.draft_reply)}
                  >
                    승인 및 게시
                  </Button>
                </Card>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              현재 관리할 부정 리뷰가 없습니다.
            </Typography>
          )}
        </Paper>
      </Box>

      {/* 고객 관리 (CRM) */}
      <Box sx={{ mt: 5 }}>
        <Typography variant="h5" component="h3" gutterBottom>
          고객 관리 (CRM) 👥
        </Typography>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Tabs value={selectedCustomerTab} onChange={handleCustomerTabChange} aria-label="customer segments tabs">
            <Tab label={`VIP 고객 (${vipCustomers.length}명)`} value="VIP" />
            <Tab label={`이탈 위험 고객 (${atRiskCustomers.length}명)`} value="이탈 위험 고객" />
          </Tabs>
          <Box sx={{ mt: 2 }}>
            {selectedCustomerTab === 'VIP' && (
              <List>
                {vipCustomers.length > 0 ? (
                  vipCustomers.map((customer) => (
                    <ListItem key={customer.customer_id}>
                      <ListItemText primary={`${customer.name} (ID: ${customer.customer_id})`} secondary={`총 지출: ${customer.total_spend}원, 총 주문: ${customer.total_orders}건`} />
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">VIP 고객이 없습니다.</Typography>
                )}
              </List>
            )}
            {selectedCustomerTab === '이탈 위험 고객' && (
              <Box>
                <List>
                  {atRiskCustomers.length > 0 ? (
                    atRiskCustomers.map((customer) => (
                      <ListItem key={customer.customer_id}>
                        <ListItemText primary={`${customer.name} (ID: ${customer.customer_id})`} secondary={`총 지출: ${customer.total_spend}원, 총 주문: ${customer.total_orders}건`} />
                      </ListItem>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">이탈 위험 고객이 없습니다.</Typography>
                  )}
                </List>
                {atRiskCustomers.length > 0 && (
                  <Button
                    variant="contained"
                    color="warning"
                    sx={{ mt: 2 }}
                    onClick={handleSendCouponToAtRiskCustomers}
                  >
                    15% 할인쿠폰 전체 발송
                  </Button>
                )}
              </Box>
            )}
          </Box>
        </Paper>
      </Box>

      {/* 여기에 다른 관리자 대시보드 컴포넌트들이 추가될 예정 */}
      <Typography variant="body1" sx={{ mt: 4 }}>
        여기에 다른 관리자 대시보드 컴포넌트들이 들어갈 예정입니다.
      </Typography>
    </Box>
  );
};

export default AdminDashboard;