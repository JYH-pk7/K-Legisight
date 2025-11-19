import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, EyeOff, Mail, Lock } from "lucide-react";
import { Link, useNavigate } from 'react-router-dom'; 
import { Checkbox } from "@/components/ui/checkbox";
import { supabase } from '@/lib/supabaseClient' 

export function LoginForm() {
    const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    rememberMe: false,
  });

  // src/pages/LoginForm.jsx (HÀM MỚI)

const handleSubmit = async (e) => { // <-- "async" 추가
  e.preventDefault();

  // state에서 이메일, 비밀번호 가져오기 (lấy email, password từ state)
  // (Bà hãy đảm bảo state của bà tên là `email` và `password` nha)

  // ----- SUPABASE 명령어 시작 -----
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });

    if (error) {
      // Supabase 오류 발생 시 (ví dụ: Sai mật khẩu)
      throw error;
    }

    // 오류가 없는 경우 (Nếu không lỗi)
    alert("로그인 성공!"); 
    console.log("Dữ liệu trả về (User):", data.user);
    navigate('/'); // 로그인 후 홈으로 이동

 } catch (error) {
  // "Lọc" lỗi và dịch sang tiếng Hàn
  if (error.message === "Invalid login credentials") {
    alert("이메일 또는 비밀번호가 잘못되었습니다."); // "Email hoặc Mật khẩu không đúng."
  } else {
    // Nếu là lỗi khác (ví dụ: lỗi mạng), thì báo lỗi chung
    alert("로그인 오류: " + error.message);
  }
  console.error("상세 오류:", error);
}
  // ----- SUPABASE 명령어 끝 -----
};

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-0">
        <CardHeader className="space-y-2 text-center pb-3 pt-6">
          {/* Logo Text Only */}
          <div className="flex items-center justify-center">
            <h1 className="text-3xl tracking-tight">
              <span className="text-blue-900">K-</span>
              <span className="text-slate-800">LegiSight</span>
            </h1>
          </div>
          <div className="h-0.5 w-16 bg-gradient-to-r from-blue-900 via-red-600 to-blue-900 mx-auto rounded-full"></div>
          
          <div>
            <CardTitle className="text-slate-800 text-xl">로그인</CardTitle>
          </div>
        </CardHeader>

        <CardContent className="px-8 pb-6">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="space-y-1">
              <div className="flex items-center gap-1.5">
                <Mail size={14} className="text-slate-600" />
                <Label htmlFor="email" className="text-slate-700 text-sm">
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
                className="border-slate-300 focus:border-blue-900 focus:ring-blue-900 h-9 text-sm"
              />
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-1.5">
                <Lock size={14} className="text-slate-600" />
                <Label htmlFor="password" className="text-slate-700 text-sm">
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
                  className="border-slate-300 focus:border-blue-900 focus:ring-blue-900 pr-10 h-9 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={formData.rememberMe}
                  onCheckedChange={(checked) => handleChange("rememberMe", checked === true)}
                  className="border-slate-400 data-[state=checked]:bg-blue-900 data-[state=checked]:border-blue-900"
                />
                <label
                  htmlFor="remember"
                  className="text-xs text-slate-600 cursor-pointer"
                >
                  로그인 상태 유지
                </label>
              </div>
              <a href="#" className="text-xs text-blue-900 hover:underline">
                비밀번호 찾기
              </a>
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-900 to-blue-800 hover:from-blue-800 hover:to-blue-700 text-white shadow-lg mt-4 h-9 transition-all duration-200 hover:shadow-xl text-sm"
            >
              로그인
            </Button>

            <div className="text-center text-xs text-slate-600 pt-3">
              계정이 없으신가요?{" "}
              <Link to="/register" className="text-blue-900 hover:underline transition-colors">
                회원가입
                </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}