# Gerobug — Development Pipeline

How code moves from an editor to a production server, and how git branches are
managed. The model is gitflow-lite: `feature/*` → `development` →
(PR + CI gate) → `main` → production pull-deploy.

```
feature/x ──merge──▶ development ──PR (CI green + staging pass)──▶ main
    ▲                    │                                          │
    └── branched from ───┘                       production pulls ──┘
                                                 via gerobug.sh → UPDATE
```

## Environments

| Environment | Branch | Role |
|---|---|---|
| DEV | `feature/*` | Your working clone. The only place code is edited. |
| STAGING | branch under test | A disposable full-stack Docker environment. Pull-only. |
| CI | every push + PR | ruff (correctness rules) + Django checks + test suite. |
| PRODUCTION | `main` | Deployed only via `./gerobug.sh` → UPDATE. |

## Branch rules

- **`main`** — production. Permanently deployable; production pulls its tip.
  Receives merges **only** from `development` (via PR with CI green) or
  `hotfix/*`. Never commit to it directly.
- **`development`** — integration branch. Feature branches merge here
  directly. Keep it green.
- **`feature/<name>`** — one per feature or non-urgent fix. Branch from
  `development`; delete after merging.
- **`hotfix/<name>`** — urgent production fix. Branch from `main`, PR back to
  `main`, then merge `main` into `development` so the fix isn't lost.
- Never commit from a staging clone. It has no authority; reset or re-clone it
  freely.
- CI only triggers on `main`, `development`, `feature/**` and pull requests —
  other branch prefixes get no CI.
- Migrations are gitignored and regenerate at container boot
  (`docker-entrypoint.sh`) — never hand-write or commit migration files.
  Data backfills belong in `dashboards/apps.py` `ready()`.

## 1. Develop

```bash
git checkout development
git pull origin development
git checkout -b feature/my-change
# ...edit, then:
git add -A
git commit -m "feat: my change"
git push -u origin feature/my-change   # CI runs on feature/** pushes
```

Run the checks locally before pushing:

```bash
ruff check gerobug_dashboard gerobug_web
cd gerobug_dashboard && python manage.py test
```

The test suite needs a reachable PostgreSQL (the hostname `db`, as in
`docker-compose.yml`) and a `gerobug_host` file at the repository root.

## 2. Stage

Use a second, disposable clone — never your working one. Hard-sync it to the
branch under test and bring the stack up:

```bash
git fetch origin
git checkout feature/my-change
git reset --hard origin/feature/my-change
docker compose up --build -d
```

Untracked runtime state (`db_data/`, `log/`, `migrations/`, `secrets/`)
survives the reset. To reset the staging database instead: `docker compose
down`, delete `db_data/`, bring the stack back up. Staging secrets are
generated on first run and then left untouched — regenerating
`POSTGRES_PASSWORD` would break the already-initialized `db_data/` volume.

**Smoke-test checklist** (run every time before promoting):

- [ ] `docker compose ps` — all four services up (`nginx`, `web`,
      `dashboard`, `db`), none restarting.
- [ ] Public site loads (rules, guidelines, hall of fame render).
- [ ] Dashboard login works on port 6320 as `geromin` (password in
      `gerobug_dashboard/secrets/gerobug_secret.env`).
- [ ] Kanban board renders; moving a report between columns persists after
      refresh.
- [ ] Open a report detail page — attachments and the severity calculator
      links render.
- [ ] Settings pages load, all tabs.
- [ ] `docker compose logs dashboard --tail 50` — no tracebacks.
- [ ] Whatever the feature branch changed, exercise it specifically.
- [ ] (When a mailbox is configured) send a test report email; it appears as a
      new BugReport and the auto-reply arrives.

## 3. Integrate

```bash
git checkout development
git pull origin development
git merge --no-ff feature/my-change
git push origin development
git branch -d feature/my-change
git push origin --delete feature/my-change
```

If several features landed since the last staging pass, re-stage
`development` itself (same procedure as step 2, branch = `development`).

## 4. Release

Gate: CI green on `development` **and** the staging checklist passed against
current `development`.

```bash
gh pr create --base main --head development --title "Release: <summary>"
# review the diff, wait for CI, then merge (merge commit, not squash)
```

Use a merge commit so `main` keeps the individual feature history.

## 5. Deploy

```bash
ssh <user>@<server>
cd /path/to/gerobug

# ALWAYS back up the database first — migrations are forward-only.
docker compose exec -T db pg_dump -U gerobug gerobug_db > ~/gerobug_backup_$(date +%F).sql

./gerobug.sh    # choose option 2) UPDATE
```

UPDATE pulls `origin/main`, backs up runtime files (logo, mail templates,
report files, `gerobug_host`) out of the running container, rebuilds the
stack, and regenerates/applies migrations on boot.

**Post-deploy verification:**

- [ ] `docker compose ps` — all services up.
- [ ] Dashboard login works over the VPN/allowlisted route.
- [ ] Public page loads over HTTPS.
- [ ] `docker compose logs -f --tail 100` — clean startup, mail poller running
      (`geromail` thread messages), no tracebacks.

## Hotfix (exception path)

```bash
git checkout main
git pull origin main
git checkout -b hotfix/broken-thing
# ...fix, commit, push:
git push -u origin hotfix/broken-thing
gh pr create --base main --head hotfix/broken-thing --title "Hotfix: <summary>"
# after CI green + merge, deploy (section 5), then bring the fix back:
git checkout development
git pull origin development
git merge main
git push origin development
```

Stage the hotfix branch first if time allows; if production is down, the
PR + CI gate is the minimum bar.

## Rollback

**Code** (on the server):

```bash
cd /path/to/gerobug
git log --oneline -5                  # find last good commit
git reset --hard <last-good-sha>
docker compose up --build --force-recreate -d
```

Then revert the bad commit properly on `main` via a PR (`git revert` on a
branch → PR → merge), and `git pull` on the server to get back in sync — a
server left in reset-hard state will conflict with the next UPDATE.

**Database:** there is no migration rollback — migrations are auto-generated
and forward-only. If a deploy's schema change must be undone, restore the
pre-deploy dump:

```bash
docker compose stop dashboard web
docker compose exec -T db psql -U gerobug -c "DROP DATABASE gerobug_db WITH (FORCE); CREATE DATABASE gerobug_db OWNER gerobug;" postgres
docker compose exec -T db psql -U gerobug gerobug_db < ~/gerobug_backup_<date>.sql
docker compose start dashboard web
```

This loses everything written after the dump — which is why the dump before
every UPDATE is non-negotiable.

## Secrets

Runtime secrets are generated by `gerobug.sh` and never committed:

- `gerobug_dashboard/secrets/gerobug_secret.env` — `DJANGO_SECRET_KEY`,
  `DJANGO_SUPERUSER_PASSWORD`, `FIELD_ENCRYPTION_KEY`
- `gerobug_dashboard/secrets/db_secret.env` — `POSTGRES_PASSWORD`
- `gerobug_dashboard/gerobug_host` — tracked empty placeholder, populated
  per-deployment

`FIELD_ENCRYPTION_KEY` must be persisted. Sensitive model fields use Fernet
encryption keyed on it; if the key is lost or changed, existing ciphertext is
unrecoverable. Never read those columns via raw SQL — always through the ORM.
