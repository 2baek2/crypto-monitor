#!/usr/bin/env python3
"""
설정 도우미 스크립트
Gate.io API와 Telegram Bot 설정을 도와주는 스크립트입니다.
"""

import os
import requests


def test_gate_api():
    """Gate.io API 공개 엔드포인트를 테스트합니다."""
    print("=== Gate.io API 테스트 ===")
    try:
        # 공개 API로 BTC 가격 조회
        response = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                price = data[0]['last']
                print(f"✅ Gate.io API 연결 성공!")
                print(f"🔹 BTC 현재가: ${price}")
                return True
        print("❌ API 응답에 문제가 있습니다.")
        return False
    except Exception as e:
        print(f"❌ Gate.io API 연결 실패: {e}")
        return False


def test_telegram_bot(token, chat_id):
    """Telegram Bot을 테스트합니다."""
    print("\n=== Telegram Bot 테스트 ===")
    try:
        # Bot 정보 확인
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print("❌ 잘못된 Bot Token입니다.")
            return False
            
        bot_info = response.json()
        if not bot_info['ok']:
            print("❌ Bot Token이 유효하지 않습니다.")
            return False
            
        print(f"✅ Bot 연결 성공: @{bot_info['result']['username']}")
        
        # 테스트 메시지 발송
        message = "🤖 암호화폐 모니터링 봇 설정 테스트입니다!"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ 테스트 메시지 발송 성공!")
                return True
            else:
                print(f"❌ 메시지 발송 실패: {result['description']}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram Bot 테스트 실패: {e}")
        return False


def get_telegram_chat_id(token):
    """Telegram Chat ID를 가져오는 방법을 안내합니다."""
    print("\n=== Telegram Chat ID 가져오기 ===")
    print("1. 생성한 봇에게 메시지를 보내세요")
    print("2. 아래 URL에 접속하세요:")
    print(f"   https://api.telegram.org/bot{token}/getUpdates")
    print("3. 'chat' 항목의 'id' 값이 Chat ID입니다")
    print("")
    
    try:
        # getUpdates API 호출
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok'] and data['result']:
                print("💡 최근 대화 내역:")
                for update in data['result'][-3:]:  # 최근 3개만
                    if 'message' in update:
                        chat_id = update['message']['chat']['id']
                        username = update['message']['chat'].get('username', 'Unknown')
                        text = update['message'].get('text', '[미디어]')
                        print(f"   Chat ID: {chat_id} (@{username}) - {text[:30]}...")
            else:
                print("💡 대화 내역이 없습니다. 봇에게 먼저 메시지를 보내주세요.")
    except Exception as e:
        print(f"❌ Chat ID 조회 실패: {e}")


def create_config_file():
    """설정 파일을 생성합니다."""
    print("\n=== 설정 파일 생성 ===")
    
    config_path = "config.py"
    
    print("Telegram Bot 설정:")
    telegram_token = input("Telegram Bot Token을 입력하세요 (없으면 Enter): ").strip()
    
    if telegram_token:
        print(f"\n봇 토큰: {telegram_token[:10]}...")
        
        # Bot 토큰 테스트
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/getMe"
            response = requests.get(url, timeout=5)
            if response.status_code == 200 and response.json()['ok']:
                print("✅ 유효한 Bot Token입니다.")
                
                # Chat ID 가져오기 안내
                get_telegram_chat_id(telegram_token)
                
                chat_id = input("\nChat ID를 입력하세요 (없으면 Enter): ").strip()
                
                if chat_id:
                    print(f"Chat ID: {chat_id}")
                    # Telegram 설정 테스트
                    test_telegram_bot(telegram_token, chat_id)
            else:
                print("❌ 유효하지 않은 Bot Token입니다.")
                telegram_token = ""
                chat_id = ""
        except:
            print("❌ Bot Token 검증 중 오류 발생")
            telegram_token = ""
            chat_id = ""
    else:
        chat_id = ""
    
    print("\nGate.io API 설정 (선택사항):")
    print("공개 API만 사용할 경우 비워두어도 됩니다.")
    api_key = input("Gate.io API Key (없으면 Enter): ").strip()
    api_secret = input("Gate.io API Secret (없으면 Enter): ").strip()
    
    # config.py 파일 생성
    config_content = f'''# Gate.io API 설정 (공개 데이터만 사용하는 경우 비워두어도 됩니다)
GATE_API_KEY = "{api_key}"
GATE_API_SECRET = "{api_secret}"

# Telegram Bot 설정
TELEGRAM_BOT_TOKEN = "{telegram_token}"
TELEGRAM_CHAT_ID = "{chat_id}"

# 모니터링 설정
# 예시 조건들 - 필요에 따라 수정하세요
MONITOR_CONDITIONS = {{
    "price_change_24h_percent": {{
        "min": -15,  # 24시간 가격 변동률이 -15% 이하일 때 알림
        "max": 20    # 24시간 가격 변동률이 20% 이상일 때 알림
    }},
    "volume_change_24h": {{
        "min": 2.0   # 24시간 거래량이 2배 이상 증가했을 때 알림
    }}
}}

# 체크 주기 (분)
CHECK_INTERVAL_MINUTES = 30
'''
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"\n✅ 설정 파일이 생성되었습니다: {config_path}")
    print("\n다음 단계:")
    print("1. watchlist.py에서 관심 종목을 추가하세요")
    print("2. 'python test.py'로 설정을 테스트하세요")
    print("3. 'python crypto_monitor.py once'로 한 번 실행해보세요")
    print("4. 'python crypto_monitor.py'로 지속적 모니터링을 시작하세요")


def main():
    """메인 함수"""
    print("🚀 암호화폐 모니터링 시스템 설정 도우미\n")
    
    # Gate.io API 테스트
    test_gate_api()
    
    # 기존 설정 파일 확인
    if os.path.exists("config.py"):
        print(f"\n⚠️  기존 config.py 파일이 있습니다.")
        overwrite = input("새로 만드시겠습니까? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("설정을 취소합니다.")
            return
    
    # 설정 파일 생성
    create_config_file()


if __name__ == "__main__":
    main()
