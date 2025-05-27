import pandas as pd
import json
from collections import defaultdict

def get_address_level(name: str):
    """
    법정동명을 분석하여 시도, 시군구, 읍면동 레벨로 분리 및 각 레벨별 명칭 반환
    ~시/도: 레벨1
    ~시/군/구: 레벨2
    ~읍/면/동/가: 레벨3
    ~리: 제외
    Returns: (시도, 시군구, 읍면동, 시도명, 시군구명, 읍면동명)
    """
    parts = name.strip().split()
    if not parts:
        return None, None, None, None, None, None
    last_part = parts[-1]
    if last_part.endswith('리'):
        return None, None, None, None, None, None

    # 세종특별자치시 특수 처리
    if parts[0] == "세종특별자치시":
        if last_part.endswith(('읍', '면', '동', '가')):
            return parts[0], parts[-1], None, parts[0], parts[-1], None
        return parts[0], None, None, parts[0], None, None

    # 시도 레벨
    if last_part.endswith(('시', '도')):
        return ' '.join(parts), None, None, parts[0], None, None
    # 시군구 레벨
    if last_part.endswith(('시', '군', '구')):
        if len(parts) > 1:
            sigungu_parts = parts[1:]
            return parts[0], ' '.join(parts), None, parts[0], ' '.join(sigungu_parts), None
        return None, ' '.join(parts), None, None, parts[-1], None
    # 읍면동 레벨 (가 포함)
    if last_part.endswith(('읍', '면', '동', '가')):
        if len(parts) > 2:
            sigungu_parts = parts[1:-1]
            return parts[0], ' '.join(parts[1:-1]), parts[-1], parts[0], ' '.join(sigungu_parts), parts[-1]
        elif len(parts) > 1:
            return None, parts[0], parts[-1], None, parts[0], parts[-1]
        return None, None, parts[-1], None, None, parts[-1]
    return None, None, None, None, None, None

# CSV 파일 로드
df = pd.read_csv("국토교통부_법정동코드.csv", encoding="cp949")
df = df[df['폐지여부'] == '존재'].copy()

# 세종특별자치시 데이터 확인
sejong_data = df[df['법정동명'].str.startswith('세종특별자치시')]
print("\n=== 세종특별자치시 데이터 샘플 ===")
print(sejong_data[['법정동명', '법정동코드']].head())

# 주소 레벨 분리 및 명칭 추출
df[['시도', '시군구', '읍면동', '시도명', '시군구명', '읍면동명']] = df['법정동명'].apply(
    lambda x: pd.Series(get_address_level(x))
)

# 세종특별자치시 처리 결과 확인
sejong_processed = df[df['시도명'] == '세종특별자치시']
print("\n=== 세종특별자치시 처리 결과 ===")
print(sejong_processed[['시도명', '시군구명', '읍면동명']].head())

# 시도별 그룹화
grouped = df.groupby('시도명')

for sido_name, group in grouped:
    if pd.isna(sido_name):
        continue
        
    sido_data = {
        "code": str(group.iloc[0]['법정동코드'])[:2],
        "name": sido_name,
        "children": []
    }
    
    sigungu_dict = defaultdict(lambda: {"children": []})
    
    for _, row in group.iterrows():
        full_code = str(row['법정동코드']).zfill(10)
        sigungu = row['시군구']
        eupmyeondong = row['읍면동']
        sigungu_name = row['시군구명']
        eupmyeondong_name = row['읍면동명']
        
        # 세종특별자치시의 경우 시군구만 있는 경우도 처리
        if sido_name == "세종특별자치시":
            if pd.isna(sigungu):
                continue
            sigungu_dict[sigungu]["code"] = full_code[:5]
            sigungu_dict[sigungu]["name"] = sigungu_name
            sigungu_dict[sigungu]["children"] = []
        else:
            if pd.isna(sigungu) or pd.isna(eupmyeondong):
                continue
            sigungu_dict[sigungu]["code"] = full_code[:5]
            sigungu_dict[sigungu]["name"] = sigungu_name
            sigungu_dict[sigungu]["children"].append({
                "code": full_code,
                "name": eupmyeondong_name
            })
    
    sido_data["children"] = list(sigungu_dict.values())
    
    # 시도 이름으로 JSON 파일 저장
    json_filename = f"{sido_name}.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(sido_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 저장 완료: {json_filename}")
 