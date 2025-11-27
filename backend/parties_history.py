import re
import pandas as pd

def parse_and_process_history(file_path, output_path):
    # 1. 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 2. 설정 및 상수 정의
    # 당명 변경 기준일 (미래통합당 -> 국민의힘)
    PPP_CHANGE_DATE = "2020.09.02"
    
    # 파싱할 정당 리스트
    known_parties = [
        "더불어민주당", "국민의힘", "정의당", "국민의당", "열린민주당", 
        "기본소득당", "시대전환", "새로운미래", "개혁신당", "조국혁신당", 
        "진보당", "자유통일당", "무소속", "미래통합당", "미래한국당", 
        "더불어시민당", "한국의희망", "새진보연합", "더불어민주연합", "국민의미래"
    ]
    
    # 날짜 정규식
    date_pattern = re.compile(r'(\d{4}\.\d{1,2}\.\d{1,2})')
    
    # 기본 임기
    DEFAULT_START = "2020.05.30"
    DEFAULT_END = "2024.05.29"

    parsed_data = []
    
    # 임시 저장 변수
    current_name = None
    current_initial_party = None
    event_lines = []

    # --- 내부 함수: 의원 1명의 이력 처리 ---
    def process_member_block(name, initial_party, events):
        if not name: return

        timeline = []
        
        # 초기 정당 정제 (개행문자 등 제거)
        current_party = initial_party.split()[0] if initial_party else "무소속"
        # 만약 '미래통합당'과 '국민의힘'이 병기되어 있다면 초기값은 '미래통합당'으로 설정
        if "미래통합당" in initial_party:
            current_party = "미래통합당"
            
        current_start = DEFAULT_START
        is_active = True # 의원직 유지 여부

        # 이벤트 날짜순 정렬
        sorted_events = []
        for line in events:
            match = date_pattern.search(line)
            if match:
                # 날짜 포맷 통일 (YYYY.MM.DD) - 한자리수 월/일 보정
                ymd = match.group(1).split('.')
                formatted_date = f"{ymd[0]}.{int(ymd[1]):02d}.{int(ymd[2]):02d}"
                sorted_events.append({'date': formatted_date, 'text': line})
        
        sorted_events.sort(key=lambda x: x['date'])

        # 이벤트 순회
        for evt in sorted_events:
            d = evt['date']
            text = evt['text']

            # A. 시작일 보정 (보궐, 승계)
            if ("당선" in text and ("보궐" in text or "재선거" in text)) or "승계" in text:
                current_start = d
                continue
            
            # B. 의원직 상실/사퇴 (기록 종료)
            if any(k in text for k in ["사퇴", "상실", "무효", "사망", "제명"]) and "당적" not in text:
                if "의원직" in text or "당선" in text or "사망" in text:
                    timeline.append({
                        'name': name, 'party': current_party, 
                        'start_date': current_start, 'end_date': d
                    })
                    is_active = False
                    break

            # C. 당적 변경 감지
            next_party = None
            if "탈당" in text or ("제명" in text and "의원직" not in text):
                next_party = "무소속"
            elif any(k in text for k in ["입당", "복당", "합당", "변경", "창당"]):
                found_party = None
                for p in sorted(known_parties, key=len, reverse=True):
                    if p in text and p != "무소속":
                        found_party = p
                        break
                
                if found_party:
                    next_party = found_party
                elif "국민의힘" in text: next_party = "국민의힘"
                elif "더불어민주당" in text: next_party = "더불어민주당"

            # 당적 변경 적용
            if next_party and next_party != current_party:
                timeline.append({
                    'name': name, 'party': current_party, 
                    'start_date': current_start, 'end_date': d
                })
                current_party = next_party
                current_start = d

        # 남은 임기 저장
        if is_active:
            if current_start < DEFAULT_END:
                timeline.append({
                    'name': name, 'party': current_party, 
                    'start_date': current_start, 'end_date': DEFAULT_END
                })
        
        # --- [추가 로직] 미래통합당 -> 국민의힘 당명 변경 적용 ---
        final_timeline = []
        for item in timeline:
            p = item['party']
            s = item['start_date']
            e = item['end_date']
            
            # 조건: 당적이 '미래통합당'이고, 기간이 2020.09.02를 포함하거나 그 이후인 경우
            if p == "미래통합당":
                if s < PPP_CHANGE_DATE < e:
                    # 1. 변경 전 (미래통합당)
                    final_timeline.append({
                        'name': item['name'], 'party': '미래통합당',
                        'start_date': s, 'end_date': PPP_CHANGE_DATE
                    })
                    # 2. 변경 후 (국민의힘)
                    final_timeline.append({
                        'name': item['name'], 'party': '국민의힘',
                        'start_date': PPP_CHANGE_DATE, 'end_date': e
                    })
                elif s >= PPP_CHANGE_DATE:
                    # 이미 날짜가 지났는데 미래통합당으로 표기된 경우 국민의힘으로 수정
                    item['party'] = '국민의힘'
                    final_timeline.append(item)
                else:
                    # 변경일 이전에 끝난 경우 (그대로 유지)
                    final_timeline.append(item)
            else:
                final_timeline.append(item)

        return final_timeline

    # 3. 텍스트 파싱 루프
    for i, line in enumerate(lines):
        line = line.strip()
        clean_line = re.sub(r'\[.*?\]', '', line).strip() # 태그 제거
        if not clean_line: continue

        # 정당명 라인인지 확인
        is_party_line = False
        for p in known_parties:
            if clean_line == p or (p in clean_line and len(clean_line) < 20):
                is_party_line = True
                break
        
        if is_party_line:
            # 정당명이 나오면, 이전에 모은 데이터 처리
            if current_name:
                parsed_data.extend(process_member_block(current_name, current_initial_party, event_lines))
            
            # 새 의원 이름 찾기 (역탐색)
            prev_idx = i - 1
            found_name = ""
            while prev_idx >= 0:
                prev_text = re.sub(r'\[.*?\]', '', lines[prev_idx]).strip()
                if not prev_text:
                    prev_idx -= 1
                    continue
                # 지역구/선거구 건너뛰기
                if any(x in prev_text for x in ['구', '시', '군']) and len(prev_text) > 4:
                    prev_idx -= 1
                    continue
                # 이름 발견 (2~5글자)
                if 2 <= len(prev_text) <= 5:
                    found_name = prev_text
                break
            
            current_name = found_name
            current_initial_party = clean_line
            event_lines = []
            
        elif clean_line.startswith('*'):
            event_lines.append(clean_line)

    # 마지막 버퍼 처리
    if current_name:
        parsed_data.extend(process_member_block(current_name, current_initial_party, event_lines))

    # 4. 데이터프레임 변환 및 정렬
    if not parsed_data:
        print("데이터 추출 실패: 형식을 확인해주세요.")
        return

    df = pd.DataFrame(parsed_data)
    
    # 컬럼 순서 지정
    df = df[['name', 'party', 'start_date', 'end_date']]
    
    # CSV 저장
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"파일 생성 완료: {output_path}")

# --- 실행 ---
# 파일 경로는 실제 환경에 맞게 수정해주세요.
input_file = 'data/21대국회 임기,당적이력_나무위키.txt' 
output_file = 'data/21대국회의원_당적이력_이름순.csv'

parse_and_process_history(input_file, output_file)