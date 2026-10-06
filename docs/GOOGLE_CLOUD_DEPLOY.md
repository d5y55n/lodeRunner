# Google Cloud Compute Engine 배포

대상: Ubuntu 24.04 LTS x86_64, e2-small, Python 3.12, FastAPI/Uvicorn 1 worker,
Nginx, systemd, 로컬 Persistent Disk의 SQLite. 이 문서는 배포 준비이며 실제
GCP 리소스를 생성하거나 프로젝트/도메인/키를 설정한 기록이 아닙니다.
Scoring / Converging / UI / 기존 API 코드는 변경하지 않습니다.

## 0. 먼저 확인

현재 Windows 작업본에서 `git rev-parse --show-toplevel`은 프로젝트가 아닌
`C:/Users/82108/Desktop`을 반환했습니다. Desktop 저장소를 그대로 push하지 마세요.
프로젝트 파일만 별도의 저장소 루트로 준비하고 아래 clone 대상 URL을 사용해야 합니다.
저장소 루트에 backend, frontend, deploy, docs가 바로 있어야 합니다.
`.venv`, API 키, .env, DPAPI 파일, SQLite/WAL/SHM, 대용량 research/operational
데이터를 커밋하지 마세요. .gitignore는 이미 추적 중인 파일을 제거하지 않습니다.
push 전에 `git ls-files`와 diff로 비밀/개인 파일 포함 여부를 직접 확인하세요.
이 작업에서는 git init, commit, push 또는 기존 Git 구조 변경을 하지 않았습니다.

각 `<...>`는 사용자 값입니다. 문서의 placeholder를 바꾼 뒤 실행하세요.
서비스 설치 경로 `/opt/loderunner`와 데이터 경로 `/var/lib/loderunner`는
제공된 파일 전체가 공유하는 고정 계약입니다. 일부 파일에서만 바꾸지 마세요.

e2-small은 공유 CPU/2GiB 메모리입니다. 공개 데모/소규모 사용의 출발점이며
850일 이력 및 percentile 초기 구축의 성능/메모리는 이 VM에서 검증되지 않았습니다.
서비스는 1 worker, 수치 라이브러리 스레드 1개, MemoryHigh 1400M/Max 1700M입니다.
OOM 시 커널이 프로세스를 종료하고 systemd가 재시작할 수 있습니다. 반복 OOM이면
VM 크기를 올리세요. 워커를 늘리면 캐시/다운로드/YouTube 모니터가 중복됩니다.
원본 체결/전체 연구 작업은 이 VM에서 실행하지 마세요.

## 1. VM 및 디스크 준비 (Google Cloud Console)

- 프로젝트 `<PROJECT_ID>`, 리전/존 `<ZONE>`, 인스턴스 `<INSTANCE_NAME>`을 선택.
- Ubuntu 24.04 LTS x86_64, e2-small, 외부 IP, 네트워크 `<VPC_NETWORK>`를 사용.
- boot Persistent Disk는 우선 30GB 이상으로 준비하고 잔여 공간을 모니터링.
- VM 삭제 시에도 보존하려면 해당 디스크의 auto-delete를 끕니다. 기본 boot disk는
  VM 삭제와 함께 지워질 수 있습니다. 재부팅에 유지되는 것과 삭제 시 보존은 다릅니다.
- 더 강한 분리를 원하면 별도의 Persistent Disk를 `/var/lib/loderunner`에 먼저
  마운트하고 UUID 기반 `/etc/fstab` 등록을 완료하세요. 아래 설치 스크립트는
  디스크를 포맷하거나 마운트하지 않습니다. 이미 데이터가 있는 디스크에 mkfs 금지.
- 별도 필수 데이터 디스크에는 `nofail`로 빈 디렉터리에 조용히 시작하지 않게 하세요.
  `findmnt /var/lib/loderunner`로 확인 후 설치합니다. unit의 RequiresMountsFor가
  등록된 mount를 의존하지만, fstab 등록 자체가 빠진 상태까지 감지하지는 않습니다.
- SSH는 본인 IP 또는 IAP로 제한. HTTP는 아래 별도 태그로 허용. 8011은 공개 금지.

## 2. SSH 접속 후 OS 패키지

아래부터는 VM의 Bash에서 실행합니다. 로컬 Windows PowerShell이 아닙니다.

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv python3-pip nginx sqlite3 curl ca-certificates ufw nodejs shellcheck
python3.12 --version
node --version
```

Ubuntu nodejs는 프런트엔드 테스트용이며 서비스 실행에는 Node가 필요하지 않습니다.
추가 C 컴파일러, Java, MySQL은 필요하지 않습니다. NumPy/Pandas/PyArrow/DuckDB/
pydantic-core의 Linux CPython 3.12 x86_64 wheel이 기존 uv.lock에 포함되어 있습니다.
실제 PyPI 다운로드 가능 여부는 다음 설치 단계에서 확인합니다. wheel이 없으면
`--only-binary`가 실패하도록 두고 버전을 임의로 낮추지 마세요.

## 3. 저장소 clone

```bash
REPO_URL='<GITHUB_REPOSITORY_URL>'
DEPLOY_REF='<BRANCH_TAG_OR_COMMIT>'
sudo git clone "$REPO_URL" /opt/loderunner
sudo git -C /opt/loderunner checkout "$DEPLOY_REF"
cd /opt/loderunner
test -f backend/pyproject.toml
test -f deploy/loderunner.service
```

비공개 저장소 인증은 별도 SSH deploy key 등으로 설정하세요. 토큰을 URL에
넣거나 명령 기록/문서에 저장하지 마세요. 이미 존재하는 설치 폴더에 덮어 clone하지 않습니다.

## 4. venv / 고정 의존성 / 테스트

```bash
cd /opt/loderunner/backend
sudo python3.12 -m venv .venv
sudo .venv/bin/python -m pip install --upgrade pip
sudo .venv/bin/python -m pip install --only-binary=:all: -r requirements-linux-test.txt
sudo .venv/bin/python -m pip check
sudo .venv/bin/python -m pytest -q
cd /opt/loderunner
node --test frontend/analysis/*.test.cjs
bash -n deploy/install.sh
shellcheck deploy/install.sh
```

runtime 단독 설치는 `requirements-linux.txt`, 위 test 파일은 runtime을 포함합니다.
두 파일은 기존 uv.lock 버전 그대로이며 pyproject/lock을 새로 해석해 업데이트하지
않습니다. 패키지 업데이트는 별도 검토/회귀 테스트 후 세 파일을 함께 정합화하세요.
앱은 wheel 설치 대신 backend 작업 디렉터리에서 실행하므로 PROJECT와 정적 파일
위치가 유지됩니다. Windows `.venv`를 VM으로 복사하면 안 됩니다.

## 5. 데이터 연결 / unit / Nginx 등록

```bash
cd /opt/loderunner
sudo bash deploy/install.sh
readlink -f /opt/loderunner/data/live-dashboard
sudo -u loderunner test -w /var/lib/loderunner/live-dashboard
```

출력 경로는 `/var/lib/loderunner/live-dashboard`여야 합니다. 이 링크 하나로
BTC/심볼별 dashboard.sqlite3, acquisition/candles/snapshots, events.sqlite3,
scoring-distribution.sqlite3 및 WAL/SHM이 persistent storage에 저장됩니다.
기존 앱의 8GiB operational SQLite 예산도 이 경로를 통해 검사됩니다.
소스는 서비스 계정에 쓰기 권한을 주지 않고, systemd는 데이터 경로만 writable로 허용합니다.

스크립트는 기존 실제 data/live-dashboard 폴더가 있으면 중단합니다. 자동 삭제나
병합하지 않습니다. 기본 Ubuntu Nginx default 심볼릭 링크만 제거하고 전용 설정을
설치합니다. 기존 서비스가 있는 VM에는 적용 전에 설정을 백업/검토하세요.
env가 이미 있으면 보존합니다. 설치만 수행하며 서비스 시작/방화벽 변경은 하지 않습니다.

## 6. 환경변수 / YouTube

```bash
sudoedit /etc/loderunner/loderunner.env
sudo chown root:root /etc/loderunner/loderunner.env
sudo chmod 600 /etc/loderunner/loderunner.env
```

편집기 안에서 `YOUTUBE_API_KEY=` 오른쪽에 본인의 키를 입력합니다. `export` 금지.
빈 값이면 기존대로 'YouTube 연동 설정 필요'를 표시합니다. Linux에서는 기존 코드가
환경변수를 먼저 읽고 DPAPI를 호출하지 않습니다. Windows DPAPI 파일은 복사하지 마세요.
YouTube Data API v3를 활성화하고 키를 해당 API로 제한하세요. 서버 IP 제한을 사용할
경우 고정 외부 IP/실제 egress 주소와 일치시켜야 합니다. 키를 프런트엔드에 넣지 마세요.
로그 조회 시에도 환경변수 전체나 요청 URL에 키를 출력하지 마세요.

## 7. 방화벽 확인

VM에서 SSH 경로를 먼저 허용한 뒤 UFW를 켭니다. 현재 연결 방식이 IAP/커스텀 SSH
포트라면 그 규칙을 먼저 맞추고 두 번째 SSH 세션으로 확인하세요.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw status verbose
sudo ufw enable
sudo ufw status verbose
```

GCP VPC 방화벽도 별개입니다. 아래는 **인증된 Cloud Shell**에서 placeholder를
수정하여 실행합니다. 기존 동일 용도 규칙이 있으면 중복 생성하지 말고 확인만 합니다.

```bash
PROJECT_ID='<PROJECT_ID>'
INSTANCE_NAME='<INSTANCE_NAME>'
ZONE='<ZONE>'
VPC_NETWORK='<VPC_NETWORK>'
HTTP_RULE='<UNIQUE_HTTP_FIREWALL_RULE_NAME>'
gcloud compute instances add-tags "$INSTANCE_NAME" --project="$PROJECT_ID" --zone="$ZONE" --tags=loderunner-http
gcloud compute firewall-rules create "$HTTP_RULE" --project="$PROJECT_ID" --network="$VPC_NETWORK" --direction=INGRESS --action=ALLOW --rules=tcp:80 --source-ranges=0.0.0.0/0 --target-tags=loderunner-http
gcloud compute firewall-rules list --project="$PROJECT_ID"
```

외부 공개 HTTP의 의도적인 규칙입니다. 22 전체 공개 규칙은 만들지 않습니다.
8011/SQLite는 VPC/UFW 어디에서도 열지 마세요. IPv6 외부 공개는 별도 검토 대상입니다.

## 8. 시작 / 자동 실행 / 외부 접속

VM SSH에서:

```bash
sudo systemd-analyze verify /etc/systemd/system/loderunner.service
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now loderunner
sudo systemctl enable --now nginx
sudo systemctl reload nginx
sudo systemctl status loderunner --no-pager
curl --fail http://127.0.0.1:8011/health
curl --fail http://127.0.0.1/health
sudo ss -lntp | grep -E ':80 |:8011 '
```

8011은 127.0.0.1에서만, 80은 외부 리스너로 보여야 합니다.
다른 PC에서 `http://<EXTERNAL_IP>/`를 열고 다음도 확인합니다:

```bash
curl --fail http://<EXTERNAL_IP>/health
```

health 성공은 프로세스 상태일 뿐 시장 데이터 준비 완료를 의미하지 않습니다.
대시보드에서 BTC 초기 4TF 다운로드 완료/READY, 현재 점수, 수렴, 수동 가격,
percentile, YouTube 상태를 별도로 확인하세요. 지원 가능한 심볼만 순차 준비하고
e2-small에서 최초 여러 심볼을 동시에 요청하지 마세요. 기존 프런트엔드 timeout은
120초로 유지됐습니다. 초기 backfill 지연은 더 큰 VM/미리 준비한 데이터로 해결합니다.
Binance는 배포 리전/IP에 따라 접근이 제한될 수 있습니다. 제한을 우회하지 마세요.
Investing iframe은 클라이언트에서 외부로 직접 접속하며 제공자 경고/차단은 별도입니다.
백엔드에서 캘린더 파싱/우회하지 않습니다.

## 9. 운영 / 백업 / 재배포

```bash
sudo journalctl -u loderunner -n 100 --no-pager
sudo journalctl -u loderunner -f
sudo tail -n 100 /var/log/nginx/loderunner.error.log
sudo systemctl restart loderunner
df -h /var/lib/loderunner
free -h
sudo journalctl --disk-usage
```

앱 로그는 journald, Nginx 로그는 Ubuntu의 기본 `/etc/logrotate.d/nginx`를 사용합니다.
journald 보관 크기는 VM의 `/etc/systemd/journald.conf`에 SystemMaxUse=200M 등
운영 정책으로 제한할 수 있습니다. 영구 로그가 필요하면 Storage=persistent도 설정.
반복 실패 후 start-limit에 걸리면 원인 해결 뒤 `sudo systemctl reset-failed loderunner`.
재부팅 후 systemctl/health로 자동 시작을 검증하세요. SQLite는 재시작 뒤에도 남습니다.

SQLite 이전/백업은 앱을 정지한 상태에서 **전체 디렉터리(WAL/SHM 포함)**를 복사합니다.
실행 중 `.sqlite3` 파일만 복사하면 일관되지 않을 수 있습니다. Windows에서 이전할
때도 해당 서버를 먼저 종료합니다. DPAPI는 제외하고 키는 VM env에 따로 설정합니다.
복구 후 소유자를 loderunner:loderunner로 설정하고 각 DB에 `PRAGMA quick_check;`를 실행.

VM에서 백업 예시 (서비스가 이미 정상 실행 중일 때):

```bash
sudo systemctl stop loderunner
sudo tar -C /var/lib/loderunner -czf "/root/loderunner-$(date -u +%Y%m%dT%H%M%SZ).tar.gz" live-dashboard
sudo systemctl start loderunner
```

같은 디스크의 tar는 디스크 삭제/장애 대비 백업이 아닙니다. 별도 디스크 스냅샷 또는
권한을 제한한 외부 저장소에 주기적으로 보관하세요. 복원 훈련이 필요합니다.
연구 replay용 frozen data는 Git에 없을 수 있으며 별도 선택 배포 없이는 과거 2023
replay가 부족 오류를 낼 수 있습니다. live 데이터를 재구축할 수 있다는 것과 과거
snapshot/알림 이력 보존은 다릅니다. 업데이트 전 운영 디렉터리를 백업하세요.

업데이트는 서비스 중지 -> 정확한 새 commit checkout -> pinned dependencies 설치 ->
테스트 -> install.sh 재실행 -> nginx -t -> 서비스 시작 순서입니다. data 심볼릭 링크와
/var/lib/loderunner를 삭제하지 마세요. 자동 git clean/reset 또는 무검토 git pull은 하지 않습니다.

## 10. HTTPS 및 공개 서비스 한계

도메인 `<DOMAIN>`과 고정 IP를 준비한 뒤 DNS A를 연결하고 Nginx server_name을
해당 도메인으로 바꿉니다. 이 시점에만 GCP/UFW tcp:443을 추가 허용하고,
Ubuntu의 certbot/python3-certbot-nginx 등으로 인증서를 발급합니다. 예:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo ufw allow 443/tcp
sudo certbot --nginx -d <DOMAIN>
sudo certbot renew --dry-run
```

server_name 편집, DNS 전파, GCP 443 규칙을 먼저 완료해야 합니다. 도메인/인증서가
없는 현재 설정은 HTTP만 제공합니다. HTTP 외부 IP에서는 브라우저 알림이 secure
context 제한으로 동작하지 않을 수 있으며 HTTPS 후 확인합니다.

이 앱에는 사용자 인증/계정별 상태 분리가 없습니다. 누구나 비용이 큰 분석 요청을
할 수 있고 YouTube notification claim 상태는 방문자 간 공유됩니다. Nginx의 IP별
rate/connection limit는 최소 보호이지 분산 DoS 방어나 multi-user 보장은 아닙니다.
민감한 데이터를 올리지 말고 초기에는 소수 사용자로 제한/관찰하세요. 인증 도입은
별도 작업이며 이번 배포 준비에서 기존 기능/알림 의미를 변경하지 않았습니다.

## 검증 범위 및 공식 참고

준비 단계 로컬 회귀: Python 전체 420개, 프런트엔드 20개 테스트 통과.
기존 Starlette/httpx deprecation warning 1건은 유지됩니다.
추가 테스트는 lock/requirements 버전 및 Linux wheel 존재 여부, Linux YouTube
환경변수/빈 키 경로, unit/Nginx 안전 설정과 LF 줄바꿈을 검사합니다.
결과 XML: data/live-dashboard/deployment-tests.xml.
Git Bash의 `bash -n deploy/install.sh` 문법 검사도 통과했습니다. shellcheck와
Ubuntu nginx/systemd 검증은 실제 VM 단계에서 실행해야 합니다.

Windows 전용 DPAPI는 os.name guard 뒤에 있고 Linux 환경변수 경로가 테스트됩니다.
연구용 fullmap/run.py의 Windows 메모리 계측도 Linux resource fallback이 있습니다.
Windows .ps1 실행 스크립트는 VM에서 사용하지 않습니다. 웹 런타임에는 절대 Windows
경로 의존성이 발견되지 않았습니다. Python pathlib가 Linux 경로를 계산합니다.
로컬은 Windows이며 Linux/WSL VM이 없어 Ubuntu pip 설치, nginx -t, systemd 부팅,
GCP 네트워크 및 실제 e2-small 자원 검증은 아직 수행하지 않았습니다. 위 VM 명령은
생략할 수 없는 배포 승인 체크리스트입니다. 실제 배포 완료로 간주하지 마세요.

- [E2 machine types](https://docs.cloud.google.com/compute/docs/general-purpose-machines)
- [Persistent Disk auto-delete](https://docs.cloud.google.com/compute/docs/disks/modify-persistent-disk)
- [Uvicorn settings](https://www.uvicorn.org/settings/)
- [Nginx proxy settings](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Nginx request limiting](https://docs.nginx.com/nginx/admin-guide/security-controls/controlling-access-proxied-http)
