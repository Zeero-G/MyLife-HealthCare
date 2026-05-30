#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  MyLife Backend Test Script
#  Run this on your LOCAL machine to verify EC2 backend connectivity
# ─────────────────────────────────────────────────────────────────

EC2_IP="54.255.246.16"
DOMAIN="myhealth.jo3.org"
BASE="https://${DOMAIN}"

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
NC="\033[0m"

ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
fail() { echo -e "${RED}  ❌ $1${NC}"; }
info() { echo -e "${BLUE}  ℹ  $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠  $1${NC}"; }

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}   MyLife Backend Connectivity Tester      ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# ── Step 1: Check DNS resolution ─────────────────────────────────
echo -e "${YELLOW}[1] Checking DNS resolution for ${DOMAIN}...${NC}"
RESOLVED=$(nslookup "${DOMAIN}" 2>/dev/null | grep 'Address' | tail -1 | awk '{print $2}')
if [ "$RESOLVED" = "$EC2_IP" ]; then
  ok "DNS resolved correctly → ${RESOLVED}"
else
  warn "DNS resolves to: ${RESOLVED} (expected ${EC2_IP})"
  info "Fixing by adding entry to /etc/hosts..."
  # Remove any old entry and add correct one
  sudo sed -i "/${DOMAIN}/d" /etc/hosts
  echo "${EC2_IP} ${DOMAIN}" | sudo tee -a /etc/hosts > /dev/null
  ok "Added ${EC2_IP} ${DOMAIN} to /etc/hosts"
fi

echo ""

# ── Step 2: Check port 443 is reachable ──────────────────────────
echo -e "${YELLOW}[2] Checking if port 443 is open on EC2...${NC}"
if nc -z -w3 "${EC2_IP}" 443 2>/dev/null; then
  ok "Port 443 is OPEN on ${EC2_IP}"
else
  fail "Port 443 is CLOSED. Open it in your AWS Security Group!"
  echo ""
  info "Go to: AWS Console → EC2 → Security Groups → Inbound Rules"
  info "Add rule: Type=HTTPS, Port=443, Source=0.0.0.0/0"
  exit 1
fi

echo ""

# ── Step 3: Test HTTPS health endpoint ───────────────────────────
echo -e "${YELLOW}[3] Testing HTTPS gateway health check...${NC}"
HEALTH=$(curl -s --resolve "${DOMAIN}:443:${EC2_IP}" --connect-timeout 5 "${BASE}/health")
if echo "${HEALTH}" | grep -q '"gateway"'; then
  ok "Gateway is UP → ${HEALTH}"
else
  fail "Gateway did not respond: ${HEALTH}"
fi

echo ""

# ── Step 4: Test CORS preflight (OPTIONS) ────────────────────────
echo -e "${YELLOW}[4] Testing CORS preflight (OPTIONS request)...${NC}"
PREFLIGHT=$(curl -s -o /dev/null -w "%{http_code}" \
  --resolve "${DOMAIN}:443:${EC2_IP}" \
  -X OPTIONS "${BASE}/auth/login" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  --connect-timeout 5)
if [ "$PREFLIGHT" = "204" ]; then
  ok "CORS preflight returned 204 — CORS is configured correctly"
else
  fail "CORS preflight returned ${PREFLIGHT} (expected 204)"
fi

echo ""

# ── Step 5: Test auth/login endpoint ─────────────────────────────
echo -e "${YELLOW}[5] Testing POST /auth/login endpoint...${NC}"
LOGIN_RESP=$(curl -s -w "\n%{http_code}" \
  --resolve "${DOMAIN}:443:${EC2_IP}" \
  -X POST "${BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"email":"test@test.com","password":"test123"}' \
  --connect-timeout 5)
HTTP_CODE=$(echo "$LOGIN_RESP" | tail -1)
BODY=$(echo "$LOGIN_RESP" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
  ok "Login returned 200 OK → ${BODY}"
elif [ "$HTTP_CODE" = "401" ]; then
  ok "Auth service responded 401 (endpoint works, credentials wrong) → ${BODY}"
elif [ "$HTTP_CODE" = "422" ]; then
  ok "Auth service responded 422 (endpoint works, validation error) → ${BODY}"
else
  fail "Unexpected response ${HTTP_CODE} → ${BODY}"
fi

echo ""

# ── Step 6: Test auth/register endpoint ──────────────────────────
echo -e "${YELLOW}[6] Testing POST /auth/register endpoint...${NC}"
REG_RESP=$(curl -s -w "\n%{http_code}" \
  --resolve "${DOMAIN}:443:${EC2_IP}" \
  -X POST "${BASE}/auth/register" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"full_name":"Test User","email":"testuser_probe@test.com","password":"TestPass123","role":"patient","gender":"male"}' \
  --connect-timeout 5)
REG_CODE=$(echo "$REG_RESP" | tail -1)
REG_BODY=$(echo "$REG_RESP" | head -1)

if [ "$REG_CODE" = "200" ] || [ "$REG_CODE" = "201" ]; then
  ok "Register returned ${REG_CODE} → ${REG_BODY}"
elif [ "$REG_CODE" = "400" ] || [ "$REG_CODE" = "409" ]; then
  ok "Register service responded ${REG_CODE} (endpoint works, email may already exist) → ${REG_BODY}"
else
  fail "Unexpected response ${REG_CODE} → ${REG_BODY}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  All tests completed!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
