#!/bin/bash
pkill -9 -f "python.*backend.app"
sleep 1

unset TRANSFORMERS_OFFLINE
unset HF_HUB_OFFLINE
export TRANSFORMERS_OFFLINE=0
export HF_HUB_OFFLINE=0

echo "=================================================="
echo "🚀 ADEASY_SHORTS Backend 시작"
echo "🔧 TRANSFORMERS_OFFLINE: ${TRANSFORMERS_OFFLINE}"
echo "🔧 HF_HUB_OFFLINE: ${HF_HUB_OFFLINE}"
echo "=================================================="

cd /home/spai0432/ADEASY_SHORTS
source venv_adway/bin/activate
python -m backend.app
