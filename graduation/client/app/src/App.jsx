
// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './dashbourd';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        {/* يمكنك إضافة مزيد من الصفحات هنا حسب الحاجة */}
      </Routes>
    </Router>
  );
}

export default App;
