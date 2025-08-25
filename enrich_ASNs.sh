#!/usr/bin/env bash
# enrich_one_asn.sh (hardened)
# RIPEstat-only enrichment; reads ASNs from JSON (array or NDJSON of {"asn": <num>})
# Usage:
#   ./enrich_one_asn.sh --json FILE [--host HOST] [--user USER] [--db DB] [--bolt neo4j+s://HOST:7687]
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }

# -------- Defaults --------
HOST="${HOST:-localhost}"
USER="${USER:-neo4j}"
DB="${DB:-neo4j}"
BOLT_URI="${BOLT_URI:-neo4j+s://${HOST}:7687}"
JSON_FILE=""

# -------- Args --------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON_FILE="${2-}"; shift 2 ;;
    --host) HOST="${2-}"; shift 2 ; BOLT_URI="neo4j+s://${HOST}:7687" ;;
    --user) USER="${2-}"; shift 2 ;;
    --db)   DB="${2-}";   shift 2 ;;
    --bolt) BOLT_URI="${2-}"; shift 2 ;;
    *) die "Unknown arg: $1" ;;
  esac
done

[[ -n "${JSON_FILE}" ]] || die "Provide --json <file> with objects like: {\"asn\": 7}"
command -v jq >/dev/null || die "jq is required"
command -v curl >/dev/null || die "curl is required"
: "${NEO4J_PASS:?Set NEO4J_PASS environment variable}"
[[ -s "${JSON_FILE}" ]] || die "JSON file not found or empty: ${JSON_FILE}"

# -------- Helpers --------
# Escape a bash string as a Cypher single-quoted literal: '...'
cypher_str() {
  # Escape backslashes and single quotes for Cypher
  local s="${1//\\/\\\\}"
  s="${s//\'/\\\'}"
  printf "'%s'" "$s"
}

# Prefer local cypher-shell, else Docker
run_cypher() {
  local query="$1"; shift
  if command -v cypher-shell >/dev/null 2>&1; then
    cypher-shell -a "${BOLT_URI}" -u "${USER}" -p "${NEO4J_PASS}" -d "${DB}" "$@" "${query}"
  else
    docker run --rm -i --network host neo4j:5.26.3 cypher-shell \
      -a "${BOLT_URI}" -u "${USER}" -p "${NEO4J_PASS}" -d "${DB}" "$@" "${query}"
  fi
}

# Curl with timeout & retries
CURL="curl -fsSL --connect-timeout 5 --max-time 15 --retry 3 --retry-delay 1 --retry-connrefused"

ripe_enrich_asn() {
  local asn="$1" base="https://stat.ripe.net/data"
  local overview whois org_name country address_lines_json

  # Overview (holder/country)
  overview="$($CURL "${base}/as-overview/data.json?resource=AS${asn}")" || return 1
  org_name="$(jq -r '.data.holder // empty' <<<"$overview" || true)"
  country="$(jq -r '.data.country // empty' <<<"$overview" || true)"

  # WHOIS (address/descr lines → array, then we’ll join later)
  whois="$($CURL "${base}/whois/data.json?resource=AS${asn}" || true)"
  address_lines_json="$(
    jq -r '
      (.data.records // [])
      | flatten
      | map(select(.key|ascii_downcase=="address" or .key|ascii_downcase=="descr") | .value)
      | unique
      | map(select(.!=null and .!=""))
    ' <<<"$whois" 2>/dev/null || echo "[]"
  )"
  [[ -z "$address_lines_json" || "$address_lines_json" == "null" ]] && address_lines_json="[]"

  # Emit a compact JSON object
  jq -n --argjson asn "$asn" \
        --arg org_name "${org_name:-}" \
        --arg country   "${country:-}" \
        --argjson address_lines "${address_lines_json}" '
    {asn:$asn, org_name:$org_name, country:$country, address_lines:$address_lines}'
}

# -------- Cypher --------
read -r -d '' CYPHER <<'CYPHER_EOF'
WITH $asn AS asn,
     coalesce($org_name, "Unknown") AS org_name,
     $country AS country,
     $address_lines AS address_lines,
     $reg_source AS reg_source,
     $reg_url AS reg_url
MERGE (a:AS {asn: asn})
MERGE (o:Organization {name: org_name})
MERGE (a)-[:MANAGED_BY]->(o)
SET o.country = country,
    o.address_lines = address_lines,  // plain string
    o.reg_source = reg_source,
    o.reg_source_url = reg_url,
    o.reg_last_seen = datetime()
RETURN a.asn AS asn, o.name AS organization, o.country AS country
CYPHER_EOF

echo "Using Neo4j @ ${BOLT_URI} (db=${DB}, user=${USER})"
echo "Reading ASNs from ${JSON_FILE}"
echo

# -------- Stream ASNs safely (array or NDJSON) --------
# We stream to avoid loading everything into RAM; each ASN is handled independently.
jq -r '
  if type=="array" then .[] else . end
  | .asn
  | if type=="string" then (select(test("^[0-9]+$")) | tonumber) else . end
  | select(type=="number")
' "${JSON_FILE}" | while IFS= read -r ASN; do
  [[ -n "$ASN" ]] || continue
  echo "→ Enriching AS${ASN} via RIPEstat…"

  # Guard block so a failure here doesn't abort the whole file
  if ! DATA="$(ripe_enrich_asn "$ASN")"; then
    warn "RIPEstat error for AS${ASN}, skipping"
    continue
  fi

  # Extract fields; guard jq to avoid aborting the loop
  ORG_NAME="$(jq -r '.org_name // empty' <<<"$DATA" 2>/dev/null || true)"
  COUNTRY="$(jq -r '.country // empty' <<<"$DATA" 2>/dev/null || true)"
  ADDR_STR="$(
    jq -r '
      .address_lines
      | if type=="array" then join(", ")
        elif type=="string" then .
        else "" end
    ' <<<"$DATA" 2>/dev/null || echo ""
  )"
  REG_URL="https://stat.ripe.net/data/as-overview?resource=AS${ASN}"

  # Build safely-escaped Cypher parameter literals
  P_ASN="--param asn=${ASN}"
  P_ORG="--param org_name=$(cypher_str "${ORG_NAME}")"
  P_CTY="--param country=$(cypher_str "${COUNTRY}")"
  P_ADDR="--param address_lines=$(cypher_str "${ADDR_STR}")"
  P_SRC="--param reg_source='ripe-stat'"
  P_URL="--param reg_url=$(cypher_str "${REG_URL}")"

  if ! run_cypher "${CYPHER}" "$P_ASN" "$P_ORG" "$P_CTY" "$P_ADDR" "$P_SRC" "$P_URL" >/dev/null; then
    warn "Neo4j write failed for AS${ASN}, skipping"
    continue
  fi

  echo "  ✓ Updated AS${ASN} (${ORG_NAME:-Unknown}${COUNTRY:+, ${COUNTRY}})"
done

echo
echo "All done."
