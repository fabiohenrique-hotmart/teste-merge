# generate new token: https://github.com/settings/tokens/new
export GITHUB_OAUTH_TOKEN=%GITHUB_OAUTH_TOKEN%

WORKDIR=$(pwd)

rm -f "$WORKDIR/dist/all-hotmart-components.yaml"
touch "$WORKDIR/dist/all-hotmart-components.yaml"

git-xargs \
  --loglevel DEBUG \
  --branch-name backstage \
  --repos "$WORKDIR/scripts/data/repos-1.txt" \
  --commit-message "[CI SKIP] Convert .heimdall to Backstage catalog" \
  --max-concurrent-repos 10 \
  --skip-archived-repos \
  python3 "$WORKDIR/scripts/catalog.py" > out.txt

# --github-org Hotmart-Org \
# --skip-pull-requests \
