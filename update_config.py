#!/usr/bin/env python3
"""
설정 관리 유틸리티 - 기존 API 키와 토큰을 보존하면서 config.py를 업데이트합니다.
"""
import os
import re
import shutil
from datetime import datetime

def extract_config_values(config_file):
    """config.py에서 실제 설정 값들을 추출합니다."""
    if not os.path.exists(config_file):
        return {}
    
    values = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 정규식으로 설정값 추출
        patterns = {
            'GATE_API_KEY': r'GATE_API_KEY\s*=\s*["\']([^"\']+)["\']',
            'GATE_API_SECRET': r'GATE_API_SECRET\s*=\s*["\']([^"\']+)["\']',
            'TELEGRAM_BOT_TOKEN': r'TELEGRAM_BOT_TOKEN\s*=\s*["\']([^"\']+)["\']',
            'TELEGRAM_CHAT_ID': r'TELEGRAM_CHAT_ID\s*=\s*["\']([^"\']+)["\']',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1)
                # 기본 예시 값이 아닌 실제 값만 저장
                if not value.startswith('your_') and value != 'your_chat_id_here':
                    values[key] = value
                    print(f"✅ 기존 {key} 발견: {value[:10]}...")
    
    except Exception as e:
        print(f"⚠️ 설정 추출 중 오류: {e}")
    
    return values

def update_config_with_preserved_values(example_file, target_file, preserved_values):
    """config.example.py를 기반으로 config.py를 생성하되 기존 값들을 보존합니다."""
    try:
        with open(example_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 기존 값들로 교체
        for key, value in preserved_values.items():
            if key == 'GATE_API_KEY':
                content = re.sub(
                    r'GATE_API_KEY\s*=\s*["\'][^"\']*["\']',
                    f'GATE_API_KEY = "{value}"',
                    content
                )
            elif key == 'GATE_API_SECRET':
                content = re.sub(
                    r'GATE_API_SECRET\s*=\s*["\'][^"\']*["\']',
                    f'GATE_API_SECRET = "{value}"',
                    content
                )
            elif key == 'TELEGRAM_BOT_TOKEN':
                content = re.sub(
                    r'TELEGRAM_BOT_TOKEN\s*=\s*["\'][^"\']*["\']',
                    f'TELEGRAM_BOT_TOKEN = "{value}"',
                    content
                )
            elif key == 'TELEGRAM_CHAT_ID':
                content = re.sub(
                    r'TELEGRAM_CHAT_ID\s*=\s*["\'][^"\']*["\']',
                    f'TELEGRAM_CHAT_ID = "{value}"',
                    content
                )
        
        # 백업 생성
        if os.path.exists(target_file):
            backup_file = f"{target_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(target_file, backup_file)
            print(f"📦 기존 config.py 백업: {backup_file}")
        
        # 새로운 config.py 생성
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {target_file} 업데이트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 설정 업데이트 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🔧 설정 관리 유틸리티")
    
    example_file = "config.example.py"
    target_file = "config.py"
    
    if not os.path.exists(example_file):
        print(f"❌ {example_file} 파일이 존재하지 않습니다.")
        return
    
    # 기존 설정값 추출
    print("\n📋 기존 설정값 추출 중...")
    preserved_values = extract_config_values(target_file)
    
    if preserved_values:
        print(f"🔑 보존할 설정 {len(preserved_values)}개 발견")
    else:
        print("ℹ️ 보존할 기존 설정이 없습니다. 새로 생성합니다.")
    
    # 설정 파일 업데이트
    print(f"\n🔄 {target_file} 업데이트 중...")
    success = update_config_with_preserved_values(example_file, target_file, preserved_values)
    
    if success:
        print("\n🎉 설정 업데이트가 완료되었습니다!")
        
        # 누락된 설정이 있는지 확인
        missing_configs = []
        required_configs = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        
        for config in required_configs:
            if config not in preserved_values:
                missing_configs.append(config)
        
        if missing_configs:
            print("\n⚠️ 다음 설정을 수동으로 입력해주세요:")
            for config in missing_configs:
                print(f"  - {config}")
            print(f"\n📝 {target_file} 파일을 편집하세요.")
        else:
            print("\n✅ 모든 필수 설정이 보존되었습니다!")
    else:
        print("\n❌ 설정 업데이트에 실패했습니다.")

if __name__ == "__main__":
    main()
