#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjI1NjM4MzUtNGUwMC00M2I2LWI1NDYtNDJhMGNmZjNjMWQ2IiwiZW1haWwiOiJlZW52eXdpdGhpbkBnbWFpbC5jb20iLCJkaXNwbGF5X25hbWUiOiJlZW52eSIsImlzX2FkbWluIjp0cnVlLCJhZG1pbl9uYW1lIjoiSXZvIiwiYWRtaW5fcm9sZSI6IkNFTyAmIENyZWF0b3IiLCJhZG1pbl9jb250ZXh0IjoiRm91bmRlZCBDaXJrZWxsaW5lLCBmb2N1c2VzIG9uIEFJIHN0cmF0ZWd5IGFuZCBwcm9kdWN0IGRldmVsb3BtZW50IiwiYWRtaW5fcHJlZmVyZW5jZXMiOiJQcmVmZXJzIHRlY2huaWNhbCBkZXRhaWxzIHdpdGggY29kZSBleGFtcGxlcy4gTGlrZXMgZGlyZWN0LCBlZmZpY2llbnQgY29tbXVuaWNhdGlvbi4iLCJhZG1pbl9pbnN0cnVjdGlvbnMiOiJBbHdheXMgcHJvdmlkZSB0ZWNobmljYWwgaW1wbGVtZW50YXRpb24gZGV0YWlscy4gSW5jbHVkZSBjb2RlIHNuaXBwZXRzIHdoZW4gcmVsZXZhbnQuIiwiZXhwIjoxNzYwNTM4NjE5LCJpYXQiOjE3NTk5MzM4MTl9.1KoywCQ-ZetwF-uYDeTBc9vRHF9STvnGWsDLlWaVZcw"

echo "Testing JWT Authentication..."
echo ""
echo "1. Test /health (should work without JWT):"
curl -s http://localhost:7777/health | jq .
echo ""

echo "2. Test /teams without JWT (should return 401):"
curl -s http://localhost:7777/teams | jq .
echo ""

echo "3. Test /teams WITH JWT (should work):"
curl -s -X GET "http://localhost:7777/teams" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

echo "4. Test POST to /teams/cirkelline/runs WITH JWT:"
curl -s -X POST "http://localhost:7777/teams/cirkelline/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=Hello&stream=false" \
  --max-time 30 | jq .
