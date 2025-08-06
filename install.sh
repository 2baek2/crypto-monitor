#!/bin/bash

# Crypto RSI Monitor 초기 설정 스크립트
echo "🚀 Crypto RSI Monitor 초기 설정을 시작합니다..."

# Python 버전 확인
echo "Python 버전 확인 중..."
python3 --version

# 가상환경 생성
if [ ! -d ".venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv .venv
fi

# 가상환경 활성화
echo "가상환경 활성화 중..."
source .venv/bin/activate

# 패키지 설치
echo "필요한 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 설정 파일 복사
if [ ! -f "config.py" ]; then
    echo "설정 파일 생성 중..."
    cp config.example.py config.py
    echo "⚠️  config.py 파일을 편집하여 텔레그램 봇 토큰과 Chat ID를 입력하세요."
else
    echo "✅ config.py 파일이 이미 존재합니다."
fi

echo ""
echo "🎉 설치가 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. config.py 파일에서 텔레그램 봇 설정을 완료하세요"
echo "2. python test.py 명령어로 설정을 테스트하세요"
echo "3. python crypto_monitor.py once 명령어로 한 번 실행해보세요"
echo "4. python crypto_monitor.py 명령어로 지속적 모니터링을 시작하세요"
echo ""
