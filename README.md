# K-Legisight
대한민국 제21대 국회 의안/법률/의원별 정보 및 의사결정 예측 모델과 그 플랫폼
<p>(최종 수정일: 2025/11/27)</p>

<br></br>
## Database Schema (Supabase)
이 프로젝트는 국회의원 활동 데이터와 감성 분석 결과를 효율적으로 관리하기 위해 다음과 같이 설계되었습니다.

| Table | Column | Type | Description |
| :--- | :--- | :--- | :--- |
| **Members** | `id` | UUID (PK) | 국회의원 고유 번호 |
| | `name` | Varchar | 의원 성명 |
| | `party` | Varchar | 소속 정당 |
| **Speeches** | `id` | BigInt (PK) | 발언 고유 ID |
| | `member_id` | UUID (FK) | Members 테이블 참조 |
| | `content` | Text | 크롤링된 발언 본문 |
| **Sentiment** | `id` | BigInt (PK) | 분석 결과 ID |
| | `speech_id` | BigInt (FK) | Speeches 테이블 참조 |
| | `score` | Float | 감성 분석 점수 (-1.0 ~ 1.0) |

<br><p>현재 Supabase 무료 티어 유지 정책으로 인해 라이브 데이터베이스는 비활성화 상태입니다. <p>
<p>그러므로 개략적인 데이터 모델링 구조는 위 스키마 표를 참조해 주시기 바랍니다.</p>
