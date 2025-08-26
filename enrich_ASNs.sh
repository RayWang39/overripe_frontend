#!/usr/bin/env bash
# enrich_ASNs.sh — RIPE-DB–only ASN enrichment into Neo4j (concurrent, resilient)
set -Eeuo pipefail
trap 'rc=$?; echo "ERR($rc) line $LINENO: $BASH_COMMAND" >&2; exit $rc' ERR

die()  { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARN:  $*" >&2; }

# -------- Defaults --------
HOST="${HOST:-localhost}"
DB_USER="${NEO4J_USER:-neo4j}"
DB="${DB:-neo4j}"
BOLT_URI="${BOLT_URI:-neo4j+s://${HOST}:7687}"
JSON_FILE=""
CONCURRENCY="${CONCURRENCY:-8}"  # RIPE-DB is OK with modest parallelism

# -------- Args --------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON_FILE="${2-}"; shift 2 ;;
    --host) HOST="${2-}"; BOLT_URI="neo4j+s://${HOST}:7687"; shift 2 ;;
    --user) DB_USER="${2-}"; shift 2 ;;
    --db)   DB="${2-}"; shift 2 ;;
    --bolt) BOLT_URI="${2-}"; shift 2 ;;
    --concurrency|-j) CONCURRENCY="${2-}"; shift 2 ;;
    *) die "Unknown arg: $1" ;;
  esac
done

echo "Using Neo4j @ ${BOLT_URI} (db=${DB}, user=${DB_USER})"
[[ -n "${JSON_FILE}" ]] || die "Provide --json <file> (objects like: {\"asn\": 7})"
command -v jq     >/dev/null || die "jq is required"
command -v curl   >/dev/null || die "curl is required"
command -v flock  >/dev/null || die "flock (util-linux) is required"
command -v xargs  >/dev/null || die "xargs is required"
: "${NEO4J_PASS:?Set NEO4J_PASS environment variable}"
[[ -s "${JSON_FILE}" ]] || die "JSON file not found or empty: ${JSON_FILE}"
jq empty "${JSON_FILE}" >/dev/null || die "Invalid JSON in ${JSON_FILE}"

# -------- Helpers --------
cypher_str() { local s="${1//\\/\\\\}"; s="${s//\'/\\\'}"; printf "'%s'" "$s"; }

run_cypher() {
  local query="$1"; shift
  if command -v cypher-shell >/dev/null 2>&1; then
    cypher-shell -a "${BOLT_URI}" -u "${DB_USER}" -p "${NEO4J_PASS}" -d "${DB}" "$@" "${query}"
  else
    command -v docker >/dev/null 2>&1 || die "cypher-shell not found and Docker not available"
    docker run --rm -i --network host neo4j:5.26.3 cypher-shell \
      -a "${BOLT_URI}" -u "${DB_USER}" -p "${NEO4J_PASS}" -d "${DB}" "$@" "${query}"
  fi
}

# Strong curl defaults; RIPE-DB sometimes hiccups
CURL="curl -sS --connect-timeout 5 --max-time 30 --retry 7 --retry-all-errors --retry-delay 2 --retry-connrefused"
RIPE_DB_BASE="https://rest.db.ripe.net/ripe"

# -------- Ensure uniqueness constraints --------
ensure_constraints() {
  echo "Ensuring Neo4j uniqueness constraints…"
  run_cypher "CREATE CONSTRAINT as_asn_unique IF NOT EXISTS FOR (a:AS) REQUIRE a.asn IS UNIQUE;" >/dev/null 2>&1 || true
  run_cypher "CREATE CONSTRAINT org_key_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.key IS UNIQUE;" >/dev/null 2>&1 || true
}
ensure_constraints

# -------- Cypher template (MERGE on Organization.key; do not clobber with empties) --------
get_cypher() {
cat <<'EOF'
WITH
  $asn           AS asn,
  $org_key       AS org_key,
  $org_name      AS org_name,
  $country       AS country,
  $address_lines AS address_lines,
  $reg_source    AS reg_source,
  $reg_url       AS reg_url

MERGE (a:AS {asn: asn})
MERGE (o:Organization {key: org_key})
MERGE (a)-[:MANAGED_BY]->(o)

SET
  o.name = coalesce(o.name, org_name),
  o.country = CASE
                WHEN country IS NOT NULL AND country <> ''
                  THEN coalesce(country, o.country)
                ELSE o.country
              END,
  o.address_lines = CASE
                      WHEN address_lines IS NOT NULL AND address_lines <> ''
                        THEN coalesce(address_lines, o.address_lines)
                      ELSE o.address_lines
                    END,
  // Prefer RIPE-DB as authoritative for source fields
  o.reg_source     = reg_source,
  o.reg_source_url = reg_url,
  o.reg_last_seen  = datetime()
RETURN a.asn AS asn, o.key AS org_key, o.name AS organization, o.country AS country, o.address_lines AS address
EOF
}

# -------- Progress (thread-safe) --------
IS_TTY=0; [ -t 1 ] && IS_TTY=1
PROG_LOCK="$(mktemp -u)"; : >"$PROG_LOCK"
PROG_CNT_FILE="$(mktemp)"; echo 0 >"$PROG_CNT_FILE"

render_progress_locked() {
  local cur="$1" total="$2"
  (( IS_TTY == 0 )) && return 0
  local width=40 pct=0
  (( total > 0 )) && pct=$(( cur * 100 / total ))
  local filled=$(( pct * width / 100 ))
  local empty=$(( width - filled ))
  printf "\r[%.*s%*s] %3d%% (%d/%d)" \
    "$filled" "========================================" \
    "$empty" "" "$pct" "$cur" "$total"
}
progress_tick() {
  local total="$1"
  flock "$PROG_LOCK" -c "
    cur=\$(cat '$PROG_CNT_FILE'); cur=\$((cur+1)); echo \$cur > '$PROG_CNT_FILE'
    $(typeset -f render_progress_locked)
    render_progress_locked \"\$cur\" \"$total\"
  " || true
}
finish_progress() { (( IS_TTY == 1 )) && echo ""; }

# -------- RIPE-DB enrichment (aut-num -> organisation -> org details) --------
ripe_db_enrich_asn() {
  local asn="$1"
  local aut_url="${RIPE_DB_BASE}/aut-num/AS${asn}.json"
  local org_id org_url org_json org_name country addr_str

  # Backoff helper with jitter
  backoff() {
    local s="$1"; awk -v s="$s" -v j="$(awk -v r="$RANDOM" 'BEGIN{srand(r); print rand()*0.2}')" 'BEGIN{printf "%.3f", s+j}'
  }

  # Fetch aut-num to find organisation id
  local tries=0 wait=0.5 aut_json
  while (( tries < 6 )); do
    if aut_json="$($CURL "$aut_url")"; then break; fi
    tries=$((tries+1)); sleep "$(backoff "$wait")"; wait=$(awk -v w="$wait" 'BEGIN{printf "%.3f", (w*2 > 16 ? 16 : w*2)}')
  done
  [[ -n "${aut_json:-}" ]] || return 1

  org_id="$(
    jq -r '
      .objects.object[0].attributes.attribute[]
      | select(.name|ascii_downcase=="org" or .name|ascii_downcase=="organisation")
      | .value
      ' <<<"$aut_json" 2>/dev/null | head -n1
  )"
  [[ -n "${org_id}" ]] || return 2  # no org id on this aut-num

  # Fetch organisation object
  org_url="${RIPE_DB_BASE}/organisation/${org_id}.json"
  tries=0; wait=0.5
  while (( tries < 6 )); do
    if org_json="$($CURL "$org_url")"; then break; fi
    tries=$((tries+1)); sleep "$(backoff "$wait")"; wait=$(awk -v w="$wait" 'BEGIN{printf "%.3f", (w*2 > 16 ? 16 : w*2)}')
  done
  [[ -n "${org_json:-}" ]] || return 3

  org_name="$(
    jq -r '
      .objects.object[0].attributes.attribute[]
      | select(.name|ascii_downcase=="org-name") | .value
    ' <<<"$org_json" 2>/dev/null | head -n1
  )"
  country="$(
    jq -r '
      .objects.object[0].attributes.attribute[]
      | select(.name|ascii_downcase=="country") | .value
    ' <<<"$org_json" 2>/dev/null | head -n1
  )"
  addr_str="$(
    jq -r '
      [ .objects.object[0].attributes.attribute[]
        | select(.name|ascii_downcase=="address") | .value
      ] | map(select(.!=null and .!="")) | join(", ")
    ' <<<"$org_json" 2>/dev/null
  )"

  # Emit TSV: org_key (ORG-…), org_name, country, address_string, reg_url
  printf '%s\t%s\t%s\t%s\t%s\n' "$org_id" "${org_name:-}" "${country:-}" "${addr_str:-}" "${org_url}"
}

# -------- Count & stream --------
ASN_COUNT="$(
  jq -r '
    if type=="array" then .[] else . end
    | .asn
    | if type=="string" then (select(test("^[0-9]+$")) | tonumber) else . end
    | select(type=="number")
  ' "${JSON_FILE}" | wc -l | tr -d ' '
)"
echo "Found ${ASN_COUNT} ASNs"
[[ "${ASN_COUNT}" -gt 0 ]] || die "No ASNs extracted."

# -------- Worker --------
process_one() {
  local ASN="$1"
  # small stagger to avoid bursts
  sleep "$(awk -v r="$RANDOM" 'BEGIN{srand(r); printf "%.3f", 0.02 + rand()*0.10}')"

  local row org_key org_name country addr_str reg_url
  if ! row="$(ripe_db_enrich_asn "$ASN")"; then
    warn "RIPE-DB error for AS${ASN}, skipping"
    progress_tick "${ASN_COUNT}"
    return 0
  fi

  # Split TSV safely
  IFS=$'\t' read -r org_key org_name country addr_str reg_url <<<"$row"

  # Build params (cypher-shell on your host expects 'name => value')
  local PARAMS=(
    --param "asn => ${ASN}"
    --param "org_key => $(cypher_str "${org_key}")"
    --param "org_name => $(cypher_str "${org_name}")"
    --param "country => $(cypher_str "${country}")"
    --param "address_lines => $(cypher_str "${addr_str}")"   # string per your requirement
    --param "reg_source => 'RIPE-DB'"
    --param "reg_url => $(cypher_str "${reg_url}")"
  )

  if ! run_cypher "$(get_cypher)" "${PARAMS[@]}" >/dev/null; then
    warn "Neo4j write failed for AS${ASN}"
  fi
  progress_tick "${ASN_COUNT}"
}

export -f process_one ripe_db_enrich_asn run_cypher cypher_str get_cypher warn render_progress_locked progress_tick
export BOLT_URI DB_USER DB NEO4J_PASS CURL RIPE_DB_BASE ASN_COUNT PROG_LOCK PROG_CNT_FILE IS_TTY

# -------- Fan-out --------
jq -r '
  if type=="array" then .[] else . end
  | .asn
  | if type=="string" then (select(test("^[0-9]+$")) | tonumber) else . end
  | select(type=="number")
' "${JSON_FILE}" \
| xargs -P "${CONCURRENCY}" -n 1 bash -c 'process_one "$1"' _

finish_progress
echo
echo "Done."
