#!/bin/bash

# Docker를 사용하여 Crypto Monitor를 한 번만 실행하는 스크립트

set -e

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Crypto Monitor - 단일 실행 (Docker)${NC}"
echo "========================================"

# 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. docker-run.sh를 먼저 실행해주세요."
    exit 1
fi

# config.py 확인
if [ ! -f "config.py" ]; then
    echo "⚠️  config.py 파일이 없습니다. docker-run.sh를 먼저 실행해주세요."
    exit 1
fi

echo -e "${BLUE}🔨 Docker 이미지 빌드 중...${NC}"
docker-compose build crypto-monitor

echo -e "${BLUE}🚀 한 번만 실행 중...${NC}"
docker-compose run --rm crypto-monitor python crypto_monitor.py once

echo -e "${GREEN}✅ 실행 완료!${NC}"
