#!/bin/sh
# N100 の cron から10分おきに実行。JR東日本は GitHub Actions からの取得を 403 で拒否するため N100 で取る。
cd "$(dirname "$0")" || exit 1
[ "$(TZ=Asia/Tokyo date +%Y%m%d)" -le 20261128 ] || exit 0
git pull -q --rebase || exit 1
python3 -I status.py || exit 1
git add status.json
git commit -qm "update status" || exit 0
git push -q
