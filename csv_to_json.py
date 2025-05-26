import pandas as pd
import json
from collections import defaultdict

# CSV 파일 로드
df = pd.read_csv("국토교통부_법정동코드.csv", encoding="cp949")
df = df[df['폐지여부'] == '존재'].copy()

# 주소 분리 함수 (3단계: 시도, 시군구, 읍면동)
def split_address_three_levels(name):
    parts = name.strip().split()
    if len(parts) < 2:
        return parts[0], None, None
    elif len(parts) == 2:
        return parts[0], parts[1], None
    else:
        return parts[0], ' '.join(parts[1:-1]), parts[-1]

df[['시도', '시군구', '읍면동']] = df['법정동명'].apply(lambda x: pd.Series(split_address_three_levels(x)))

# 시도별 그룹화
grouped = df.groupby('시도')

# 시도별 JSON 파일 생성
for sido, group in grouped:
    # 시도 코드 추출 (안전하게 처리)
    sido_code = str(group['법정동코드'].values[0])[:2] if not group.empty else ""
    
    sido_data = {
        "code": sido_code,
        "name": sido,
        "children": []
    }
    
    sigungu_dict = defaultdict(lambda: {"children": []})
    
    for _, row in group.iterrows():
        full_code = str(row['법정동코드'])
        sigungu = row['시군구']
        eupmyeondong = row['읍면동']
        
        if pd.isna(sigungu) or pd.isna(eupmyeondong):
            continue
        
        sigungu_dict[sigungu]["code"] = full_code[:5]
        sigungu_dict[sigungu]["name"] = sigungu
        sigungu_dict[sigungu]["children"].append({
            "code": full_code,
            "name": eupmyeondong
        })
    
    sido_data["children"] = list(sigungu_dict.values())
    
    # JSON 저장
    filename = f"{sido}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(sido_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 저장 완료: {filename}")
