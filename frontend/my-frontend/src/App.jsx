// src/App.jsx (CODE MỚI HOÀN TOÀN)

import { Routes, Route, Navigate } from 'react-router-dom'
import { LoginForm } from './pages/LoginForm.jsx'
import { SignupForm } from './pages/RegisterForm.jsx' // Tên component là SignupForm
import './index.css'

function App() {
  return (
    <Routes>
      {/* Khi người ta vào "/", tự động nhảy sang "/login" */}
      <Route path="/" element={<Navigate to="/" />} /> 

      {/* Đường dẫn /login sẽ "vẽ" ra LoginForm */}
      <Route path="/login" element={<LoginForm />} />

      {/* Đường dẫn /register sẽ "vẽ" ra SignupForm */}
      <Route path="/register" element={<SignupForm />} />
    </Routes>
  )
}

export default App