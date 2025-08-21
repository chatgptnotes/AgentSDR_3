#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Force-load .env in UTF-8
load_dotenv(override=True, encoding='utf-8')

print("=== .env variables present? ===")
url = os.getenv('SUPABASE_URL')
anon = os.getenv('SUPABASE_ANON_KEY')
sr = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
print("SUPABASE_URL:", 'SET' if url else 'MISSING')
print("SUPABASE_ANON_KEY:", 'SET' if anon else 'MISSING')
print("SUPABASE_SERVICE_ROLE_KEY:", 'SET' if sr else 'MISSING')

if not (url and sr):
	print("\nMissing required vars. Fix .env and re-run.")
	exit(1)

print("\n=== Testing Supabase connection ===")
try:
	from supabase import create_client
	sb = create_client(url, sr)
	resp = sb.table('users').select('count').execute()
	print("Connection OK. Users table query returned.")
except Exception as e:
	print("Connection FAILED:", e)
	print("Hint: check keys, project URL, and that .env is UTF-8 without BOM.")
	exit(2)
