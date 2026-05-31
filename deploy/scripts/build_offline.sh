#!/bin/bash
# AUTOPS 离线部署包构建脚本
# 用法: ./build_offline.sh [output_dir]
# 产出: autops-offline-{version}.tar.gz

set -euo pipefail

VERSION=${AUTOPS_VERSION:-"1.0.0"}
OUTPUT_DIR=${1:-"/tmp/autops-offline"}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== AUTOPS 离线包构建 v${VERSION} ==="

# 1. 准备输出目录
rm -rf "$OUTPUT_DIR/autops-${VERSION}"
mkdir -p "$OUTPUT_DIR/autops-${VERSION}"/{backend,frontend,configs,deploy/scripts,data}

# 2. 后端依赖导出
echo "[1/6] 导出后端代码..."
rsync -a --exclude='__pycache__' --exclude='.venv' --exclude='*.pyc' \
  "$PROJECT_DIR/backend/" "$OUTPUT_DIR/autops-${VERSION}/backend/"

# 3. 前端构建产物
echo "[2/6] 复制前端构建产物..."
if [ -d "$PROJECT_DIR/frontend/dist" ]; then
  rsync -a "$PROJECT_DIR/frontend/dist/" "$OUTPUT_DIR/autops-${VERSION}/frontend/dist/"
else
  echo "警告: frontend/dist 不存在，请先构建前端"
fi

# 4. 配置文件
echo "[3/6] 复制配置文件..."
rsync -a "$PROJECT_DIR/configs/" "$OUTPUT_DIR/autops-${VERSION}/configs/"

# 5. 部署脚本
echo "[4/6] 复制部署脚本..."
rsync -a "$PROJECT_DIR/deploy/scripts/" "$OUTPUT_DIR/autops-${VERSION}/deploy/scripts/"

# 6. 生成pip离线包
echo "[5/6] 导出Python依赖(wheel)..."
mkdir -p "$OUTPUT_DIR/autops-${VERSION}/backend/wheels"
if [ -f "$PROJECT_DIR/backend/requirements.txt" ]; then
  if command -v pip &>/dev/null; then
    pip download -r "$PROJECT_DIR/backend/requirements.txt" \
      -d "$OUTPUT_DIR/autops-${VERSION}/backend/wheels/" \
      --prefer-binary 2>/dev/null || echo "警告: 部分wheel下载失败"
  else
    echo "警告: pip 未找到，跳过 wheel 导出"
  fi
else
  echo "警告: requirements.txt 不存在，跳过 wheel 导出"
fi

# 7. 打包
echo "[6/6] 打包..."
cd "$OUTPUT_DIR"
tar czf "autops-offline-${VERSION}.tar.gz" "autops-${VERSION}/"
SIZE=$(du -sh "autops-offline-${VERSION}.tar.gz" | cut -f1)

# 写入版本信息
echo "$VERSION" > "$OUTPUT_DIR/autops-${VERSION}/VERSION"

echo ""
echo "=== 构建完成 ==="
echo "输出: $OUTPUT_DIR/autops-offline-${VERSION}.tar.gz"
echo "大小: $SIZE"
