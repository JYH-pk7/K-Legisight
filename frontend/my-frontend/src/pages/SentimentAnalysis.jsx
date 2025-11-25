// src/pages/LegislatorAnalysis.jsx
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, RotateCcw, Download, Users, FileText, ChevronRight, Bot } from "lucide-react";

const DISTRICTS = {
  "서울": ["서울 강남구갑", "서울 강남구병", "서울 강남구을", "서울 강동구갑", "서울 강동구을", "서울 강북구갑", "서울 강북구을", "서울 강서구갑", "서울 강서구병", "서울 강서구을", "서울 관악구갑", "서울 관악구을", "서울 광진구갑", "서울 광진구을", "서울 구로구갑", "서울 구로구을", "서울 금천구", "서울 노원구갑", "서울 노원구을", "서울 도봉구갑", "서울 도봉구을", "서울 동대문구갑", "서울 동대문구을", "서울 동작구갑", "서울 동작구을", "서울 마포구갑", "서울 마포구을", "서울 서대문구갑", "서울 서대문구을", "서울 서초구갑", "서울 서초구을", "서울 성북구갑", "서울 성북구을", "서울 송파구갑", "서울 송파구병", "서울 송파구을", "서울 양천구갑", "서울 양천구을", "서울 영등포구갑", "서울 영등포구을", "서울 용산구", "서울 은평구갑", "서울 은평구을", "서울 종로구", "서울 중구성동구갑", "서울 중구성동구을", "서울 중랑구갑", "서울 중랑구을"],
  "부산": ["부산 강서구", "부산 금정구", "부산 기장군", "부산 남구", "부산 동래구", "부산 부산진구갑", "부산 부산진구을", "부산 북구갑", "부산 북구을", "부산 사상구", "부산 사하구갑", "부산 사하구을", "부산 서구동구", "부산 수영구", "부산 연제구", "부산 영도구", "부산 중구영도구", "부산 해운대구갑", "부산 해운대구을"],
  "대구": ["대구 달서구갑", "대구 달서구병", "대구 달서구을", "대구 달성군", "대구 북구갑", "대구 북구을", "대구 서구", "대구 수성구갑", "대구 수성구을", "대구 중구남구갑", "대구 중구남구을", "대구 동구군위군갑", "대구 동구군위군을"],
  "인천": ["인천 계양구갑", "인천 남동구갑", "인천 남동구을", "인천 동구미추홀구갑", "인천 동구미추홀구을", "인천 부평구갑", "인천 부평구을", "인천 서구갑", "인천 서구을", "인천 연수구갑", "인천 연수구을", "인천 중구강화군옹진군", "인천 서구병"],
  "광주": ["광주 광산구갑", "광주 광산구을", "광주 동구남구갑", "광주 동구남구을", "광주 북구갑", "광주 북구을", "광주 서구갑", "광주 서구을"],
  "대전": ["대전 대덕구", "대전 동구", "대전 서구갑", "대전 서구을", "대전 유성구갑", "대전 유성구을", "대전 중구"],
  "울산": ["울산 남구갑", "울산 남구을", "울산 동구", "울산 북구", "울산 울주군", "울산 중구"],
  "경기": ["경기 고양시갑", "경기 고양시병", "경기 고양시을", "경기 고양시정", "경기 광명시갑", "경기 광명시을", "경기 광주시갑", "경기 광주시을", "경기 구리시", "경기 군포시갑", "경기 군포시을", "경기 김포시갑", "경기 김포시을", "경기 남양주시갑", "경기 남양주시을", "경기 부천시갑", "경기 부천시병", "경기 부천시을", "경기 성남시수정구", "경기 성남시중원구", "경기 성남시분당구갑", "경기 성남시분당구을", "경기 수원시갑", "경기 수원시무", "경기 수원시병", "경기 수원시을", "경기 수원시정", "경기 수흥시갑", "경기 수흥시을", "경기 안산시갑", "경기 안산시을", "경기 안성시", "경기 안양시동안구갑", "경기 안양시동안구을", "경기 안양시만안구", "경기 여주시양평군", "경기 오산시", "경기 용인시갑", "경기 용인시병", "경기 영인시을", "경기 용인시정", "경기 의왕시과천시", "경기 의정부시갑", "경기 의정부시을", "경기 이천시", "경기 파주시갑", "경기 파주시을", "경기 평택시갑", "경기 평택시을", "경기 포천시가평군", "경기 화성시갑", "경기 화성시병", "경기 화성시을", "경기 화성시정", "경기 안산시병", "경기 동두천시양주시연천군을", "경기 동두천시양주시연천군갑", "경기 하남시을", "경기 하남시갑", "경기 하남시병"],
  "강원": ["강원 강릉시", "강원 동해시태백시삼척시정선군", "강원 속초시인제군고성군양양군", "강원 원주시갑", "강원 원주시을", "강원 춘천시철원군화천군양구군을", "강원 춘천시철원군화천군양구군갑", "강원 홍천군횡성군영월군평창군"],
  "충북": ["충북 보은군옥천군영동군괴산군", "충북 제천시단양군", "충북 증평군진천군음성군", "충북 청주시상당구", "충북 청주시서원구", "충북 청주시청원구", "충북 청주시흥덕구", "충북 충주시"],
  "충남": ["충남 공주시부여군청양군", "충남 논산시계룡시금산군", "충남 당진시", "충남 보령시서천군", "충남 서산시태안군", "충남 아산시갑", "충남 천안시갑", "충남 천안시병", "충남 천안시을", "충남 홍성군예산군"],
  "전북": ["전북 익산시갑", "전북 익산시을", "전북 전주시갑", "전북 전주시병", "전북 전주시을", "전북 정읍시고창군", "전북 군산시김제시부안군을", "전북 군산시김제시부안군갑", "전북 남원시장수군임실군순창군", "전북 완주군진안군무주군"],
  "전남": ["전남 고흥군보성군장흥군강진군", "전남 나주시화순군", "전남 담양군함평군영광군장성군", "전남 목포시", "전남 순천시광양시곡성군구례군을", "전남 여수시갑", "전남 여수시을", "전남 영암군무안군시안군", "전남 해남군완도군진도군"],
  "경북": ["경북 경산시", "경북 경주시", "경북 고령군성주군칠곡군", "경북 구미시갑", "경북 구미시을", "경북 김천시", "경북 상주시문경시", "경북 안동시예천군", "경북 영천시청도군", "경북 포항시남구올릉군", "경북 포항시북구", "경북 영주시영양군봉화군", "경북 의성군청송군영덕군울진군"],
  "경남": ["경남 거제시", "경남 김해시갑", "경남 김해시을", "경남 밀양시의령군함안군창녕군", "경남 사천시남해군하동군", "경남 산청군함양군거창군합천군", "경남 양산시갑", "경남 양산시을", "경남 진주시갑", "경남 진주시을", "경남 창원시마산합포구", "경남 창원시마산회원구", "경남 창원시성산구", "경남 창원시의창구", "경남 창원시진해구", "경남 통영시고성군"],
  "제주": ["제주 제주시갑", "제주 제주시을", "제주 서귀포시"],
  "세종": ["세종 세종특별자치시갑", "세종 세종특별자치시을"]
};

export function SentimentAnalysis() {
  const [selectedCity, setSelectedCity] = useState('all');
  const currentDistricts = DISTRICTS[selectedCity] || [];

  // State cho ô tìm kiếm Dự luật
  const [billName, setBillName] = useState("");
  // State lưu kết quả tìm kiếm (Ban đầu là null)
  const [searchResults, setSearchResults] = useState(null);

  // Hàm giả lập việc tìm kiếm (Sau này nối API thật vào đây)
  const handleSearch = () => {
    // Tạo dữ liệu giả để hiển thị
    const mockData = [
      { id: 1, name: "김철수 (Kim Chul-soo)", party: "더불어민주당", region: "서울 종로구", img: "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", bill: billName || "AI 기본법", sentiment: "협력", score: 85 },
      { id: 2, name: "이영희 (Lee Young-hee)", party: "국민의힘", region: "부산 해운대구갑", img: "https://api.dicebear.com/7.x/avataaars/svg?seed=Aneka", bill: billName || "AI 기본법", sentiment: "비협력", score: 24 },
      { id: 3, name: "박민수 (Park Min-soo)", party: "조국혁신당", region: "비례대표", img: "https://api.dicebear.com/7.x/avataaars/svg?seed=John", bill: billName || "AI 기본법", sentiment: "중립", score: 52 },
    ];
    setSearchResults(mockData);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-slate-900 border-l-4 border-blue-900 pl-4">
            의원별 법안 분석 
          </h1>
          <Button className="bg-blue-900 hover:bg-blue-800">
            <Download className="w-4 h-4 mr-2" /> 리포트 다운로드
          </Button>
        </div>

        {/* --- FILTER SECTION --- */}
        <Card className="border rounded-sm shadow-sm bg-white">
          <CardContent className="p-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">

              {/* Các bộ lọc cũ */}
              <FilterItem label="대수">
                <Select defaultValue="=21">
                  <SelectTrigger>제21대<SelectValue placeholder="21대" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="21">제21대</SelectItem>
                  </SelectContent>
                </Select>
              </FilterItem>

              <FilterItem label="의원명">
                <Input placeholder="이름 입력" className="h-10" />
              </FilterItem>

              <FilterItem label="정당">
                <Select>
                  <SelectTrigger><SelectValue placeholder="전체" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="소속정당 전체">소속정당 전체</SelectItem>
                    <SelectItem value="100">무소속</SelectItem>
                    <SelectItem value="101">더불어민주당</SelectItem>
                    <SelectItem value="102">더불어시민당</SelectItem>
                    <SelectItem value="103">열린민주당</SelectItem>
                    <SelectItem value="104">미래통합당</SelectItem>
                    <SelectItem value="105">미래한국당</SelectItem>
                    <SelectItem value="106">국민의힘</SelectItem>
                    <SelectItem value="107">정의당</SelectItem>
                    <SelectItem value="108">국민의당</SelectItem>
                    <SelectItem value="109">새로운미래</SelectItem>
                    <SelectItem value="110">개혁신당</SelectItem>
                    <SelectItem value="111">조국혁신당</SelectItem>
                    <SelectItem value="112">자유통일당</SelectItem>
                    <SelectItem value="113">기본소득당</SelectItem>
                    <SelectItem value="114">진보당</SelectItem>
                    <SelectItem value="115">시대전환</SelectItem>
                    
                  </SelectContent>
                </Select>
              </FilterItem>

                <FilterItem label="위원회">
                    <Select>
                        <SelectTrigger><SelectValue placeholder="전체" /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="전체">전체</SelectItem>
                            <SelectItem value="1">과학기술정보방송통신위원회</SelectItem>
                            <SelectItem value="2">교육위원회</SelectItem>
                            <SelectItem value="3">국방위원회</SelectItem>
                            <SelectItem value="4">국토교통위원회</SelectItem>
                            <SelectItem value="5">국회운영위원회</SelectItem>
                            <SelectItem value="6">기획재정위원회</SelectItem>
                            <SelectItem value="7">농림축산식품해양수산위원회</SelectItem>
                            <SelectItem value="8">문화체육관광위원회</SelectItem>
                            <SelectItem value="9">법제사법위원회</SelectItem>
                            <SelectItem value="10">보건복지위원회</SelectItem>
                            <SelectItem value="11">산업통상자원중소벤처기업위원회</SelectItem>
                            <SelectItem value="12">여성가족위원회</SelectItem>
                            <SelectItem value="13">연금개혁특별위원회</SelectItem>
                            <SelectItem value="14">예산결산특별위원회</SelectItem>
                            <SelectItem value="15">외교통일위원회</SelectItem>
                            <SelectItem value="16">윤리특별위원회</SelectItem>
                            <SelectItem value="17">정무위원회</SelectItem>
                            <SelectItem value="18">정보위원회</SelectItem>
                            <SelectItem value="19">정치개혁특별위원회</SelectItem>
                            <SelectItem value="20">첨단전략산업특별위원회</SelectItem>
                            <SelectItem value="21">행정안전위원회</SelectItem>
                            <SelectItem value="22">환경노동위원회</SelectItem>
                            <SelectItem value="23">인구위기특별위원회</SelectItem>
                            <SelectItem value="24">기후위기특별위원회</SelectItem>
                        </SelectContent>

                    </Select>
                </FilterItem>  

              <FilterItem label="지역선거구">
                <div className="flex gap-2 w-full">
                   <Select defaultValue="all" onValueChange={(value) => setSelectedCity(value)}>
                      <SelectTrigger><SelectValue placeholder="시/도" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">전체</SelectItem>
                        <SelectItem value="서울">서울</SelectItem>
                        <SelectItem value="부산">부산</SelectItem>
                        <SelectItem value="대구">대구</SelectItem>
                        <SelectItem value="인천">인천</SelectItem>
                        <SelectItem value="광주">광주</SelectItem>
                        <SelectItem value="대전">대전</SelectItem>
                        <SelectItem value="울산">울산</SelectItem>
                        <SelectItem value="경기">경기</SelectItem>
                        <SelectItem value="강원">강원</SelectItem>
                        <SelectItem value="충북">충북</SelectItem>
                        <SelectItem value="충남">충남</SelectItem>
                        <SelectItem value="전북">전북</SelectItem>
                        <SelectItem value="전남">전남</SelectItem>
                        <SelectItem value="경북">경북</SelectItem>
                        <SelectItem value="경남">경남</SelectItem>
                        <SelectItem value="제주">제주</SelectItem>
                        <SelectItem value="세종">세종</SelectItem>
                      </SelectContent>
                   </Select>
                   <Select defaultValue="all" key={selectedCity}>
                    <SelectTrigger><SelectValue placeholder="구/군" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">전체</SelectItem>
                      {currentDistricts.map((district) => (
                          <SelectItem key={district} value={district}>{district}</SelectItem>
                      ))}
                    </SelectContent>
                    </Select>
                </div>
              </FilterItem>

              <FilterItem label="성별">
                <Select>
                  <SelectTrigger><SelectValue placeholder="전체" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="m">남</SelectItem>
                    <SelectItem value="f">여</SelectItem>
                  </SelectContent>
                </Select>
              </FilterItem>
             
               <FilterItem label="연령">
                <Select>
                  <SelectTrigger><SelectValue placeholder="전체" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="u30">30세미만</SelectItem>
                    <SelectItem value="u40">30세</SelectItem>
                    <SelectItem value="u50">40세</SelectItem>
                    <SelectItem value="u60">50세</SelectItem>
                    <SelectItem value="u70">60세</SelectItem>
                    <SelectItem value="o70">70세이상</SelectItem>
                    </SelectContent>
                </Select>
              </FilterItem>

              <FilterItem label="당선횟수">
                <Select>
                  <SelectTrigger><SelectValue placeholder="전체" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="초선">초선</SelectItem>
                    <SelectItem value="재선">재선</SelectItem>
                    <SelectItem value="3선">3선</SelectItem>
                    <SelectItem value="4선">4선</SelectItem>
                    <SelectItem value="5선">5선</SelectItem>
                    <SelectItem value="6선">6선</SelectItem>
                    <SelectItem value="7선">7선</SelectItem>
                    <SelectItem value="8선">8선</SelectItem>
                    <SelectItem value="9선">9선</SelectItem>
                    <SelectItem value="10선">10선</SelectItem>
                    </SelectContent>
                </Select>
              </FilterItem>

              <FilterItem label="당선방법">
                <Select>
                  <SelectTrigger><SelectValue placeholder="전체" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="지역구">지역구</SelectItem>
                    <SelectItem value="비례대표">비례대표</SelectItem>
                    </SelectContent>
                </Select>
              </FilterItem>

              {/* 1. Ô NHẬP DỰ LUẬT (MỚI) */}
              <div className="col-span-1 md:col-span-2 lg:col-span-3 bg-blue-50 p-4 rounded-lg border border-blue-100 mb-2">
                <div className="flex items-center gap-4">
                  <label className="w-24 text-sm font-bold text-blue-900 shrink-0 flex items-center gap-2">
                    <FileText className="w-4 h-4" /> 대상 법안
                  </label>
                  <Input 
                    placeholder="분석하고 싶은 법안명을 입력하세요 (예: 인공지능 산업 육성법)" 
                    className="h-11 text-base bg-white border-blue-200 focus-visible:ring-blue-500"
                    value={billName}
                    onChange={(e) => setBillName(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex justify-center gap-2 pt-4 border-t mt-6">
              <Button className="bg-blue-900 hover:bg-blue-800 px-10 h-12 text-lg" onClick={handleSearch}>
                <Search className="w-5 h-5 mr-2" /> AI 분석 시작 
              </Button>
              <Button variant="outline" className="px-6 h-12 text-slate-600" onClick={() => {setSearchResults(null); setBillName("")}}>
                <RotateCcw className="w-4 h-4 mr-2" /> 초기화
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* --- RESULT SECTION (Phần Kết Quả) --- */}
        {/* Nếu chưa tìm kiếm thì hiện chỗ trống, nếu tìm rồi thì hiện danh sách */}
        {!searchResults ? (
          <div className="h-64 bg-slate-100 rounded-lg flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-300">
             <Search className="w-12 h-12 mb-2 opacity-50" />
             <p>검색 조건을 입력하고 "AI 분석 시작" 버튼을 눌러주세요.</p>
          </div>
        ) : (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Bot className="w-6 h-6 text-purple-600" />
                AI 분석 결과 ({searchResults.length}건)
              </h2>
              <Badge variant="outline" className="bg-white text-slate-500">
                AI Model v2.0
              </Badge>
            </div>

            {/* Danh sách kết quả */}
            <div className="grid gap-4">
              {searchResults.map((item) => (
                <Card key={item.id} className="overflow-hidden hover:shadow-md transition-shadow border-slate-200">
                  <div className="flex flex-col md:flex-row">
                    
                    {/* Cột 1: Thông tin Nghị sĩ */}
                    <div className="p-6 flex items-center gap-4 w-full md:w-1/3 border-b md:border-b-0 md:border-r border-slate-100 bg-slate-50/50">
                      <div className="w-16 h-16 rounded-full bg-white shadow-sm overflow-hidden border border-slate-200">
                        <img src={item.img} alt={item.name} className="w-full h-full object-cover" />
                      </div>
                      <div>
                        <h3 className="font-bold text-lg text-slate-800">{item.name}</h3>
                        <div className="flex flex-col text-sm text-slate-500">
                          <span className={`font-medium ${item.party === '더불어민주당' ? 'text-blue-600' : item.party === '국민의힘' ? 'text-red-600' : 'text-slate-600'}`}>
                            {item.party}
                          </span>
                          <span>{item.region}</span>
                        </div>
                      </div>
                    </div>

                    {/* Cột 2: Kết quả Phân tích Dự luật */}
                    <div className="p-6 flex-1 flex flex-col justify-center">
                      <div className="flex justify-between items-center mb-4">
                        <div>
                          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">TARGET BILL</span>
                          <div className="font-bold text-slate-800 text-lg flex items-center gap-2">
                            <FileText className="w-4 h-4 text-slate-400" />
                            {item.bill}
                          </div>
                        </div>
                        <Badge className={`text-base px-3 py-1 ${
                          item.score >= 70 ? 'bg-blue-100 text-blue-700 hover:bg-blue-100' : 
                          item.score <= 30 ? 'bg-red-100 text-red-700 hover:bg-red-100' : 
                          'bg-slate-100 text-slate-700 hover:bg-slate-100'
                        }`}>
                          {item.sentiment}
                        </Badge>
                      </div>

                      {/* Thanh Progress AI Score */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">AI 협력 지수 (Cooperation Score)</span>
                          <span className={`font-bold ${
                            item.score >= 70 ? 'text-blue-600' : item.score <= 30 ? 'text-red-600' : 'text-slate-600'
                          }`}>{item.score}/100</span>
                        </div>
                        <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-1000 ${
                              item.score >= 70 ? 'bg-blue-500' : item.score <= 30 ? 'bg-red-500' : 'bg-slate-400'
                            }`} 
                            style={{ width: `${item.score}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-slate-400 text-right pt-1">
                          * 회의록 발언 기반 감성 분석 결과
                        </p>
                      </div>
                    </div>

                    {/* Nút chi tiết */}
                    <div className="p-4 flex items-center justify-center border-l border-slate-100 w-full md:w-24 bg-slate-50/30 hover:bg-slate-100 cursor-pointer transition-colors group">
                      <ChevronRight className="w-6 h-6 text-slate-300 group-hover:text-slate-600" />
                    </div>

                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

function FilterItem({ label, children }) {
  return (
    <div className="flex items-center">
      <label className="w-24 text-sm font-bold text-slate-700 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}