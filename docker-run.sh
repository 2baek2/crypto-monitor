#!/bin/bash

# Docker Compose를 사용하여 Crypto Monitor 실행하는 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Crypto Monitor Docker Setup${NC}"
echo "=================================="

# 1. 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다. .env.example에서 복사합니다...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ .env 파일을 편집하여 실제 API 키와 설정을 입력해주세요!${NC}"
    echo -e "   nano .env 또는 vi .env"
    echo ""
fi

# 2. config.py 확인
if [ ! -f "config.py" ]; then
    echo -e "${YELLOW}⚠️  config.py 파일이 없습니다. config.example.py에서 복사합니다...${NC}"
    cp config.example.py config.py
    echo -e "${RED}❗ config.py 파일을 편집하여 실제 설정을 입력해주세요!${NC}"
    echo -e "   nano config.py 또는 vi config.py"
    echo ""
fi

# 3. 로그 디렉토리 생성
echo -e "${BLUE}📁 로그 디렉토리 생성...${NC}"
mkdir -p logs

# 4. Docker 이미지 빌드
echo -e "${BLUE}🔨 Docker 이미지 빌드 중...${NC}"
docker compose build

# 5. 컨테이너 실행
echo -e "${BLUE}🐳 컨테이너 시작 중...${NC}"
docker compose up -d

# 6. 상태 확인
echo -e "${GREEN}✅ 설정 완료!${NC}"
echo ""
echo "📊 컨테이너 상태:"
docker compose ps

echo ""
echo "📝 로그 확인:"
echo "  docker compose logs -f crypto-monitor"
echo ""
echo "🛑 중지:"
echo "  docker compose down"
echo ""
echo "🔄 재시작:"
echo "  docker compose restart"

# 7. 실시간 로그 표시 여부 묻기
read -p "실시간 로그를 보시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📋 실시간 로그 (Ctrl+C로 종료):${NC}"
    docker compose logs -f crypto-monitor
fi
