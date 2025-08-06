#!/bin/bash

# Crypto RSI Monitor 초기 설정 스크립트 (uv 사용)
echo "🚀 Crypto RSI Monitor 초기 설정을 시작합니다..."

# uv 설치 확인
echo "uv 설치 확인 중..."
if ! command -v uv &> /dev/null; then
    echo "❌ uv가 설치되지 않았습니다."
    echo "다음 명령어로 uv를 설치하세요:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "또는 macOS의 경우: brew install uv"
    exit 1
fi

echo "✅ uv 버전: $(uv --version)"

# Python 버전 확인
echo "Python 버전 확인 중..."
uv python list

# uv 가상환경 및 의존성 설치
echo "uv를 사용하여 가상환경 생성 및 패키지 설치 중..."
if [ -f "pyproject.toml" ]; then
    echo "pyproject.toml 발견 - uv sync 실행 중..."
    uv sync
else
    echo "requirements.txt 사용 - uv venv 및 uv pip install 실행 중..."
    uv venv
    uv pip install -r requirements.txt
fi

# 설정 파일 관리 (기존 설정 보존)
echo "설정 파일 관리 중..."
if [ -f "config.py" ]; then
    echo "📋 기존 config.py 발견 - 설정값 보존하며 업데이트 중..."
    uv run python update_config.py
else
    echo "📝 새로운 config.py 생성 중..."
    cp config.example.py config.py
    echo "⚠️  config.py 파일을 편집하여 텔레그램 봇 토큰과 Chat ID를 입력하세요."
fi

echo ""
echo "🎉 설치가 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. config.py 파일에서 텔레그램 봇 설정을 완료하세요"
echo "2. uv run python test/test.py 명령어로 설정을 테스트하세요"
echo "3. uv run python crypto_monitor.py once 명령어로 한 번 실행해보세요"
echo "4. uv run python crypto_monitor.py 명령어로 지속적 모니터링을 시작하세요"
echo ""
echo "📌 uv 사용법:"
echo "  - 스크립트 실행: uv run python <script_name>.py"
echo "  - 쉘 활성화: source .venv/bin/activate (또는 uv shell)"
echo "  - 패키지 추가: uv add <package_name>"
echo ""
echo "🎯 실행 도우미 스크립트:"
echo "  - ./run.sh help      # 도움말"
echo "  - ./run.sh test      # 기본 테스트"
echo "  - ./run.sh test-all  # 모든 테스트"
echo "  - ./run.sh start     # 모니터링 시작"
echo ""
