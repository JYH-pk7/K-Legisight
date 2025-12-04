# backend/database.py
import os
from supabase import create_client, Client

# --- THAY THÔNG TIN CỦA BÀ VÀO ĐÂY ---
SUPABASE_URL = "https://ufqjggevnsahhfwilvkh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmcWpnZ2V2bnNhaGhmd2lsdmtoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4MjEwMzgsImV4cCI6MjA3ODM5NzAzOH0.wSbdtofKG-VvIfJI6QZS26FB-6nH8sgmnuB71vseou4" # Cái anon key dài ngoằng

# Tạo kết nối
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)