#!/bin/bash

# Crypto Monitor 실행 도우미 (uv)

show_help() {
    echo "🚀 Crypto Monitor 실행 도우미"
    echo ""
    echo "사용법: $0 [명령어]"
    echo ""
    echo "명령어:"
    echo "  install    - 시스템 설치 및 설정"
    echo "  test       - 기본 시스템 테스트"
    echo "  test-rsi   - RSI 분석 테스트"
    echo "  test-div   - RSI 다이버전스 테스트"
    echo "  test-all   - 모든 테스트 실행"
    echo "  once       - 한 번만 모니터링 실행"
    echo "  start      - 지속적 모니터링 시작"
    echo "  config     - 설정 파일 업데이트 (기존 키 보존)"
    echo "  schedule   - 스마트 스케줄링 테스트"
    echo "  cooldown   - 쿨다운 시스템 테스트"
    echo "  help       - 이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 install    # 처음 설치"
    echo "  $0 test       # 설정 테스트"
    echo "  $0 start      # 모니터링 시작"
    echo ""
}

case "$1" in
    "install")
        echo "🔧 시스템 설치 중..."
        ./install.sh
        ;;
    "test")
        echo "🧪 시스템 테스트 중..."
        uv run --with-requirements requirements.txt python test/test.py
        ;;
    "test-rsi")
        echo "📊 RSI 분석 테스트 중..."
        uv run --with-requirements requirements.txt python test/test_rsi.py
        ;;
    "test-div")
        echo "🎯 RSI 다이버전스 테스트 중..."
        uv run --with-requirements requirements.txt python test/test_divergence.py
        ;;
    "test-all")
        echo "🔄 모든 테스트 실행 중..."
        uv run --with-requirements requirements.txt python run_tests.py
        ;;
    "once")
        echo "🎯 단일 모니터링 실행..."
        uv run --with-requirements requirements.txt python crypto_monitor.py once
        ;;
    "start")
        echo "🚀 지속적 모니터링 시작..."
        uv run --with-requirements requirements.txt python crypto_monitor.py
        ;;
    "config")
        echo "⚙️ 설정 파일 업데이트 중..."
        uv run python update_config.py
        ;;
    "schedule")
        echo "⏰ 스마트 스케줄링 테스트..."
        uv run python test/test_scheduling.py
        ;;
    "cooldown")
        echo "🛡️ 쿨다운 시스템 테스트..."
        uv run python test/test_unified_cooldown.py
        ;;
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    *)
        echo "❌ 알 수 없는 명령어: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
