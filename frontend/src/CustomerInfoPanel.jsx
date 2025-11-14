import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Divider, CircularProgress, Alert } from '@mui/material';
import axios from 'axios';

const CustomerInfoPanel = ({ customerId, inquiry }) => {
  const [customer, setCustomer] = useState(null);
  const [orders, setOrders] = useState([]);
  const [claims, setClaims] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [recommendedManual, setRecommendedManual] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!customerId) {
      setCustomer(null);
      setOrders([]);
      setClaims([]);
      setReviews([]);
      setRecommendedManual(null);
      return;
    }

    const fetchCustomerData = async () => {
      setLoading(true);
      setError(null);
      console.log(`CustomerInfoPanel: customerId (${customerId})에 대한 데이터 가져오기 시작...`);
      try {
        // 1. 고객 기본 정보 가져오기
        const customerRes = await axios.get('http://127.0.0.1:8000/api/admin/customers_by_segment?segment=All');
        console.log("CustomerInfoPanel: API 응답 받음:", customerRes);
        
        // 응답 데이터 구조 확인
        if (!customerRes.data || !Array.isArray(customerRes.data.customers)) {
            console.error("CustomerInfoPanel: 예상과 다른 데이터 구조입니다. 'customers' 배열이 없습니다.", customerRes.data);
            throw new Error("데이터 구조 오류");
        }

        const currentCustomer = customerRes.data.customers.find(c => c.customer_id === customerId);
        console.log("CustomerInfoPanel: 고객 정보 찾기 결과:", currentCustomer);
        setCustomer(currentCustomer);

      } catch (err) {
        setError('고객 정보를 불러오는 데 실패했습니다.');
        console.error('CustomerInfoPanel: 고객 정보 API 호출 또는 처리 중 심각한 오류 발생:', err);
      } finally {
        setLoading(false);
        console.log("CustomerInfoPanel: 데이터 가져오기 절차 완료.");
      }
    };

    fetchCustomerData();
  }, [customerId]);

  // AI 추천 매뉴얼 로직 (inquiry가 바뀔 때마다 실행)
  useEffect(() => {
    if (inquiry && inquiry.question_text) {
        // TODO: /api/manuals/recommend API 구현 후 호출
        // 임시로 더미 데이터 사용
        setRecommendedManual("[SM-CS-QUAL-102: 포장 누수]");
    } else {
        setRecommendedManual(null);
    }
  }, [inquiry]);

  if (loading) {
    return (
      <Paper elevation={3} sx={{ p: 2, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }

  if (!customerId) {
    return (
      <Paper elevation={3} sx={{ p: 2, height: '100%', overflowY: 'auto' }}>
        <Typography variant="h6" gutterBottom>
          고객 정보
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="body1" color="text.secondary">
          왼쪽에서 문의를 선택하면 고객 정보가 여기에 표시됩니다.
        </Typography>
      </Paper>
    );
  }
  
  if (error && !customer) {
      return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Paper elevation={3} sx={{ p: 2, height: '100%', overflowY: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        고객 정보
      </Typography>
      <Divider sx={{ mb: 2 }} />
      
      {customer ? (
        <Box>
          <Typography variant="subtitle1"><strong>고객 이름:</strong> {customer.name}</Typography>
          <Typography variant="body2" color="text.secondary">ID: {customer.customer_id}</Typography>
          <Typography variant="body1" sx={{ mt: 1 }}><strong>고객 등급:</strong> {customer.segment}</Typography>
          <Typography variant="body1"><strong>총 주문액:</strong> {customer.total_spend.toLocaleString()}원</Typography>
          <Typography variant="body1"><strong>총 주문 수:</strong> {customer.total_orders}건</Typography>
        </Box>
      ) : (
        <Typography variant="body1" color="text.secondary">
            해당 고객 정보를 찾을 수 없습니다. (ID: {customerId})
        </Typography>
      )}

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" gutterBottom>
        최근 주문 내역
      </Typography>
      {orders.length > 0 ? (
        <Box>
          {orders.slice(0, 3).map(order => ( // 최근 3개만 표시
            <Typography key={order.product_order_id} variant="body2">
              - {order.product_name} ({order.order_status})
            </Typography>
          ))}
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary">최근 주문 내역이 없습니다.</Typography>
      )}

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" gutterBottom>
        과거 클레임
      </Typography>
      {claims.length > 0 ? (
        <Box>
            {claims.slice(0, 3).map(claim => ( // 최근 3개만 표시
                <Typography key={claim.product_order_id} variant="body2">
                - {claim.claim_reason} ({claim.claim_type})
                </Typography>
            ))}
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary">
            과거 클레임 내역이 없습니다.
        </Typography>
      )}

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" gutterBottom>
        과거 리뷰
      </Typography>
      {reviews.length > 0 ? (
        <Box>
            {reviews.slice(0, 3).map(review => ( // 최근 3개만 표시
                <Typography key={review.review_id} variant="body2">
                - "{review.review_text.substring(0, 15)}..." (⭐ {review.rating}점)
                </Typography>
            ))}
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary">
            과거 리뷰 내역이 없습니다.
        </Typography>
      )}

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" gutterBottom>
        AI 추천 매뉴얼
      </Typography>
      {recommendedManual ? (
        <Typography variant="body2" color="text.secondary">
            현재 문의는 <strong>{recommendedManual}</strong>와(과) 일치할 수 있습니다.
        </Typography>
      ) : (
        <Typography variant="body2" color="text.secondary">
            추천 매뉴얼이 없습니다.
        </Typography>
      )}
    </Paper>
  );
};

export default CustomerInfoPanel;
