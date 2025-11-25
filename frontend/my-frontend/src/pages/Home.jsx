// src/pages/Home.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from "@/components/ui/button"; // Giữ lại 1 dòng thôi
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge"; 
import { Search, Activity, TrendingUp } from "lucide-react";

export function Home() {
    const [stats, setStats] = useState({
        sentiment: { cooperation: 0, nonCooperation: 0 },
        prediction: { billName: "로딩 중...", passProbability: 0, status: "..." }
});
    useEffect(() => {
    const fetchData = async () => {
      try {
        // Gọi vào Server Python (FastAPI) - Cổng 8000
        const res = await fetch('http://localhost:8000/api/dashboard-stats');
        
        // Kiểm tra nếu mạng lỗi hoặc server lỗi
        if (!res.ok) {
          throw new Error(`네워트 응답 문제가 있습니다: ${res.status}`);
        }

        const data = await res.json();
        setStats(data); // Cập nhật dữ liệu mới
      } catch (error) {
        console.error("데이더가 가져간 문제 오류:", error);
        // Không dùng biến 'response' hay 'res' ở đây để tránh lỗi ReferenceError
      }
    };

    fetchData();
  }, []);
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      
      {/* --- 1. HERO SECTION --- */}
      <header className="relative bg-slate-900 text-white overflow-hidden pb-32">
        
        {/* Background Decoration */}
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
           <div className="absolute right-0 top-0 w-96 h-96 bg-blue-500 rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/2"></div>
           <div className="absolute left-0 bottom-0 w-64 h-64 bg-purple-500 rounded-full blur-3xl transform -translate-x-1/2 translate-y-1/2"></div>
        </div>

        {/* Navbar */}
        <nav className="relative container mx-auto px-6 py-6 flex justify-between items-center z-10">
          <div className="text-2xl font-bold tracking-tighter flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Activity className="text-white w-5 h-5" />
            </div>
            <span>
              <Link to ="/home">
              K-LegiSight
              </Link>
              </span>
          </div>
          
          <div className="flex gap-3">
            <Link to="/login">
              <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-800">
                로그인
              </Button>
            </Link>
            <Link to="/register">
              <Button className="bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20">
                회원가입
              </Button>
            </Link>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative container mx-auto px-6 mt-20 text-center z-10">
          
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-tight mb-6">
            국회 데이터를 <span className="text-blue-500">예측</span>하고<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              입법 흐름
            </span>을 파악하세요.
          </h1>
          
          <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-10">
            K-LegiSight는 국회 회의록 빅데이터를 분석하여<br className="hidden md:block" />
            의원의 발언 성향과 법안의 통과 가능성을 투명하게 제공합니다.
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative flex items-center bg-white rounded-full p-2 shadow-2xl">
                <Search className="ml-4 text-slate-400 h-6 w-6" />
                <input 
                  type="text" 
                  placeholder="궁금한 의원이나 법안을 검색해보세요..." 
                  className="w-full p-3 text-lg text-slate-900 placeholder-slate-400 bg-transparent border-none outline-none"
                />
                <Button className="rounded-full px-8 h-12 bg-slate-900 hover:bg-slate-800 text-white font-medium text-lg">
                  검색
                </Button>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap justify-center gap-2 text-sm text-slate-400">
              <span>추천 검색어:</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full cursor-pointer hover:text-white transition-colors">#AI산업육성법</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full cursor-pointer hover:text-white transition-colors">#세법개정안</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full cursor-pointer hover:text-white transition-colors">#법제사법위원회</span>
            </div>
          </div>
        </div>
      </header>

    {/* --- 2. FEATURES SECTION: 2 Model Chính (Đã thêm Link) --- */}
      <main className="container mx-auto px-6 -mt-20 relative z-20 pb-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          
          {/* Model 1: Sentiment Analysis -> Bấm vào nhảy sang trang Analysis */}
          <Link to="/sentiment" className="block group">
            <Card className="h-full shadow-xl border-0 hover:-translate-y-1 transition-transform duration-300 bg-white/95 backdrop-blur cursor-pointer group-hover:ring-2 group-hover:ring-blue-500/50">
              <CardHeader className="pb-2">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                  <Activity className="w-6 h-6 text-blue-600 group-hover:text-white transition-colors" />
                </div>
                <CardTitle className="text-2xl font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                  감성 분석 (Sentiment)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 mb-6 text-lg">
                  회의록 발언을 AI로 분석하여 의원의 태도(협력/비협력/중립)를 명확하게 시각화합니다.
                </p>
                
                {/* Dữ liệu động */}
                <div className="space-y-3 pointer-events-none"> {/* pointer-events-none để không bị conflict click */}
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-slate-600">협력</span>
                    <span className="text-blue-600">{stats.sentiment.cooperative}%</span>
                  </div>
                  <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                    <div className="bg-blue-500 h-full rounded-full transition-all duration-1000" style={{ width: `${stats.sentiment.cooperative}%` }}></div>
                  </div>
                  
                  <div className="flex justify-between text-sm font-medium mt-2">
                    <span className="text-slate-600">비협력</span>
                    <span className="text-red-500">{stats.sentiment.non_cooperative}%</span>
                  </div>
                  <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                    <div className="bg-red-500 h-full rounded-full transition-all duration-1000" style={{ width: `${stats.sentiment.non_cooperative}%` }}></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Model 2: Prediction -> Bấm vào nhảy sang trang Analysis */}
          <Link to="/Sentiment" className="block group">
            <Card className="h-full shadow-xl border-0 hover:-translate-y-1 transition-transform duration-300 bg-white/95 backdrop-blur cursor-pointer group-hover:ring-2 group-hover:ring-purple-500/50">
              <CardHeader className="pb-2">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-purple-600 transition-colors">
                  <TrendingUp className="w-6 h-6 text-purple-600 group-hover:text-white transition-colors" />
                </div>
                <CardTitle className="text-2xl font-bold text-slate-800 group-hover:text-purple-600 transition-colors">
                  입법 예측 (Prediction)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 mb-6 text-lg">
                  협력도와 발언 데이터를 학습한 AI 모델이 법안의 본회의 통과 확률을 예측합니다.
                </p>
                
                {/* Dữ liệu động */}
                <div className="bg-slate-50 p-5 rounded-xl border border-slate-100 pointer-events-none">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-slate-700">{stats.prediction.bill_name}</span>
                    <Badge variant="secondary" className="bg-purple-100 text-purple-700 hover:bg-purple-100">
                      {stats.prediction.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>통과 확률</span>
                    <span className="text-purple-600 font-bold text-lg">{stats.prediction.probability}% 유력</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full">
                      <div className="bg-purple-600 h-full rounded-full transition-all duration-1000" style={{ width: `${stats.prediction.probability}%` }}></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>

        </div>
      </main>

      {/* --- 3. VALUE SECTION  --- */}
      <section className="py-24 bg-white border-t border-slate-100">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              데이터로 만드는 <span className="text-blue-600">투명한 입법 생태계</span>
            </h2>
            <p className="text-slate-500">
              K-LegiSight는 다양한 분야에서 새로운 가치를 창출합니다.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Card 1: Cử tri */}
            <div className="group p-8 rounded-2xl bg-slate-50 hover:bg-blue-50 border border-slate-100 hover:border-blue-100 transition-all duration-300">
              <div className="w-14 h-14 bg-white rounded-xl flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform">
                <span className="text-3xl">🗳️</span>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-3">스마트한 유권자</h3>
              <p className="text-slate-600 leading-relaxed text-sm">
                우리 지역구 의원이 법안 심사에서<br/>
                어떤 태도를 보였는지 데이터로 확인하고,<br/>
                현명한 투표 권리를 행사하세요.
              </p>
            </div>

            {/* Card 2: Báo chí */}
            <div className="group p-8 rounded-2xl bg-slate-50 hover:bg-purple-50 border border-slate-100 hover:border-purple-100 transition-all duration-300">
              <div className="w-14 h-14 bg-white rounded-xl flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform">
                <span className="text-3xl">📰</span>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-3">데이터 저널리즘</h3>
              <p className="text-slate-600 leading-relaxed text-sm">
                객관적인 수치와 시각화 자료를 통해<br/>
                복잡한 정치 이슈를 독자들에게<br/>
                쉽고 명확하게 전달할 수 있습니다.
              </p>
            </div>

            {/* Card 3: Nghiên cứu */}
            <div className="group p-8 rounded-2xl bg-slate-50 hover:bg-orange-50 border border-slate-100 hover:border-orange-100 transition-all duration-300">
              <div className="w-14 h-14 bg-white rounded-xl flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform">
                <span className="text-3xl">🎓</span>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-3">입법 정책 연구</h3>
              <p className="text-slate-600 leading-relaxed text-sm">
                감성 분석 데이터와 입법 예측 모델을<br/>
                활용하여 정량적이고 심도 있는<br/>
                정치·행정 연구를 수행하세요.
              </p>
            </div>

          </div>
          
          {/* Banner đăng ký miễn phí */}
          <div className="mt-16 bg-slate-900 rounded-2xl p-8 md:p-12 text-center relative overflow-hidden">
            <div className="relative z-10">
              <h3 className="text-2xl font-bold text-white mb-4">지금 바로 국회 데이터를 확인해보세요</h3>
              <p className="text-slate-400 mb-8">회원가입 후 더 많은 분석 리포트를 무료로 열람할 수 있습니다.</p>
              <Link to="/register">
                <Button className="bg-white text-slate-900 hover:bg-slate-100 font-bold px-8 h-12 text-base">
                  무료 회원가입 하기
                </Button>
              </Link>
            </div>
            {/* Background deco */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/20 rounded-full blur-3xl translate-x-1/2 -translate-y-1/2"></div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
             <div className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-500" />
                K-LegiSight
             </div>
             <p className="text-sm">대한민국 정치 데이터의 새로운 기준</p>
          </div>
          <div className="text-center md:text-right text-sm">
            <p>국립부경대학교 디지털 스마트 부산 아카데미 부경대 7기</p>
            <p className="mt-1 opacity-60">금상첨화</p>
          </div>
        </div>
      </footer>

    </div>
  );
}
