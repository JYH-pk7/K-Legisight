import React from "react";
import { useState } from "react"; 
import { Eye, EyeOff, User, Mail, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { supabase } from '@/lib/supabaseClient' 
import { Link, useNavigate } from 'react-router-dom';

export function SignupForm() {
    const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleSubmit = async (e) => { // <-- THÊM "async"
  e.preventDefault();

  // Lấy email, password từ state (giống hệt code của bà)
  const { email, password, confirmPassword, fullName } = formData;

  // (Bà nên thêm 1 cái "if" ở đây để kiểm tra 
  if (password !== confirmPassword) { 
    alert("비밀번호가 일치하지 않습니다!"); 
    return; 
}
  
  // ----- LỆNH CỦA SUPABASE BẮT ĐẦU TỪ ĐÂY -----
  try {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        // Tùy chọn: Gửi "Họ Tên" (fullName) lên Supabase luôn
        data: {
          full_name: fullName 
        }
      }
    });

    if (error) {
      // Nếu Supabase báo lỗi (ví dụ: email đã tồn tại)
      throw error;
    }

    // Nếu không lỗi
    alert("회원가입 성공! 이메일을 확인하여 계정을 인증해주세요.");
    console.log("반환된 데이터:", data);
    navigate('/login');

  } catch (error) {
    // Báo lỗi cho người dùng
    alert("회원가입 오류: " + error.message);
    console.error("상세 오류:", error);
  }
  // ----- KẾT THÚC LỆNH CỦA SUPABASE -----
};

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-0">
        <CardHeader className="space-y-1.5 text-center pb-2 pt-4">
          {/* Logo Text Only */}
          <div className="flex items-center justify-center">
            <h1 className="text-2xl tracking-tight">
              <span className="text-blue-900">K-</span>
              <span className="text-slate-800">LegiSight</span>
            </h1>
          </div>
          <div className="h-0.5 w-14 bg-gradient-to-r from-blue-900 via-red-600 to-blue-900 mx-auto rounded-full"></div>
          
          <div>
            <CardTitle className="text-slate-800 text-lg">회원가입</CardTitle>
          </div>
        </CardHeader>

        <CardContent className="px-8 pb-5">
          <form onSubmit={handleSubmit} className="space-y-2.5">
            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <User size={13} className="text-slate-600" />
                <Label htmlFor="fullName" className="text-slate-700 text-xs">
                  이름
                </Label>
              </div>
              <Input
                id="fullName"
                type="text"
                placeholder="이름을 입력하세요"
                value={formData.fullName}
                onChange={(e) => handleChange("fullName", e.target.value)}
                required
                className="border-slate-300 focus:border-blue-900 focus:ring-blue-900 h-8 text-sm"
              />
            </div>

            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <Mail size={13} className="text-slate-600" />
                <Label htmlFor="email" className="text-slate-700 text-xs">
                  이메일
                </Label>
              </div>
              <Input
                id="email"
                type="email"
                placeholder="example@email.com"
                value={formData.email}
                onChange={(e) => handleChange("email", e.target.value)}
                required
                className="border-slate-300 focus:border-blue-900 focus:ring-blue-900 h-8 text-sm"
              />
            </div>

            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <Lock size={13} className="text-slate-600" />
                <Label htmlFor="password" className="text-slate-700 text-xs">
                  비밀번호
                </Label>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="비밀번호를 입력하세요"
                  value={formData.password}
                  onChange={(e) => handleChange("password", e.target.value)}
                  required
                  className="border-slate-300 focus:border-blue-900 focus:ring-blue-900 pr-9 h-8 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700"
                >
                  {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <Lock size={13} className="text-slate-600" />
                <Label htmlFor="confirmPassword" className="text-slate-700 text-xs">
                  비밀번호 확인
                </Label>
              </div>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="비밀번호를 다시 입력하세요"
                  value={formData.confirmPassword}
                  onChange={(e) => handleChange("confirmPassword", e.target.value)}
                  required
                  className="border-slate-300 focus:border-blue-900 focus:ring-blue-900 pr-9 h-8 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700"
                >
                  {showConfirmPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-900 to-blue-800 hover:from-blue-800 hover:to-blue-700 text-white shadow-lg mt-3 h-8 transition-all duration-200 hover:shadow-xl text-sm"
            >
              가입하기
            </Button>

            <div className="text-center text-xs text-slate-600 pt-2">
              이미 계정이 있으신가요?{" "}
              <Link to= "/login" className="text-blue-900 hover:underline transition-colors">
                로그인
                </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
