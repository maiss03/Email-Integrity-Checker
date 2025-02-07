// src/components/Dashboard.jsx
import React from 'react';
import { Box, Button, Typography, List, ListItem, ListItemText, Divider } from '@mui/material';
import { Link } from 'react-router-dom';

// Sidebar Component
const Sidebar = () => {
  return (
    <Box sx={{ width: 250, backgroundColor: '#F8B6D1', height: '100vh', paddingTop: 2 }}>
      <List>
        <ListItem button component={Link} to="/inbox">
          <ListItemText primary="البريد الوارد" />
        </ListItem>
        <Divider />
        <ListItem button component={Link} to="/emailview">
          <ListItemText primary="عرض الإيميل" />
        </ListItem>
      </List>
    </Box>
  );
};

// Inbox Component
const Inbox = () => {
  return (
    <Box sx={{ padding: 3 }}>
      <Typography variant="h4" sx={{ color: '#F8B6D1', marginBottom: 2 }}>البريد الوارد</Typography>
      <Button variant="contained" sx={{ backgroundColor: '#F8B6D1', color: '#fff', marginBottom: 2 }}>إنشاء بريد جديد</Button>
      <List>
        <ListItem>
          <ListItemText
            primary="أحمد"
            secondary="تقرير الأداء الشهري"
          />
        </ListItem>
        {/* باقي الرسائل */}
      </List>
    </Box>
  );
};

// EmailView Component
const EmailView = () => {
  return (
    <Box sx={{ padding: 3 }}>
      <Typography variant="h5" sx={{ color: '#F8B6D1' }}>موضوع الرسالة</Typography>
      <Typography sx={{ marginTop: 2 }}>محتوى الرسالة...</Typography>
      <Typography sx={{ color: '#4CAF50', fontWeight: 'bold', marginTop: 2 }}>تم التحقق: SPF/DKIM/Hash</Typography>
      <Typography sx={{ color: '#FF4D4D', fontWeight: 'bold', marginTop: 2 }}>تم التلاعب بالبريد</Typography>
    </Box>
  );
};

// Dashboard Component (Main Dashboard Layout)
const Dashboard = () => {
  return (
    <Box sx={{ display: 'flex' }}>
      <Sidebar />
      <Box sx={{ flexGrow: 1, padding: 3 }}>
        <Typography variant="h3" sx={{ color: '#F8B6D1' }}>اللوحة الرئيسية</Typography>
      </Box>
    </Box>
  );
};

export default Dashboard;
