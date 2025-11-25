// src/App.jsx

import { Routes, Route, Navigate } from 'react-router-dom'
import { LoginForm } from './pages/LoginForm.jsx'
import { SignupForm } from './pages/RegisterForm.jsx' 
import { Home } from './pages/Home.jsx';
import {SentimentAnalysis} from './pages/SentimentAnalysis.jsx'; 
import './index.css'

function App() {
  return (
    <Routes>
      {/* Khi người ta vào "/", tự động nhảy sang "/home" */}
      <Route path="/" element={<Navigate to="/home" />} /> 

      {/* Đường dẫn /login sẽ "vẽ" ra LoginForm */}
      <Route path="/login" element={<LoginForm />} />

      {/* Đường dẫn /register sẽ "vẽ" ra SignupForm */}
      <Route path="/register" element={<SignupForm />} />

      {/* Đường dẫn /home sẽ "vẽ" ra Home */}
      <Route path="/home" element={<Home />} />
      
      {/* Đường dẫn /sentiment sẽ "vẽ" ra Sentimentanalysis */}
      <Route path="/sentiment" element={<SentimentAnalysis />} />
    </Routes>
  )
}

export default App