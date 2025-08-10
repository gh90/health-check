#!/bin/bash

# 설정
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICES=("health_check")

# 사용법 출력
usage() {
    echo "사용법: $0 [서비스명|all]"
    echo "예시:"
    echo "  $0 all              # 모든 서비스 배포"
    echo "  $0 health_check    # health_check만 배포"
    exit 1
}

# 대상 확인
TARGET="$1"
if [ -z "$TARGET" ]; then
    usage
fi

# 유효한 서비스명인지 확인
if [ "$TARGET" != "all" ] && [[ ! " ${SERVICES[@]} " =~ " $TARGET " ]]; then
    echo "❌ 유효하지 않은 서비스 이름: $TARGET"
    usage
fi

# Git pull (선택 시에만)
echo "📥 Git pull: origin master"
cd "$PROJECT_DIR"
git pull origin master || { echo "❌ git pull 실패"; exit 1; }

# 도커 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    exit 1
fi
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

# 서비스 실행 함수
deploy_service() {
    local service="$1"
    echo "🚀 $service 배포 중..."
    docker compose build "$service"
    docker compose up -d "$service"
}

# 배포 실행
if [ "$TARGET" == "all" ]; then
    for service in "${SERVICES[@]}"; do
        deploy_service "$service"
    done
else
    deploy_service "$TARGET"
fi

echo "✅ 배포 완료!"
