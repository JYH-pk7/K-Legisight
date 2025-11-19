// src/lib/supabaseClient.js

import { createClient } from '@supabase/supabase-js'

// Dán URL và "anon" key của bà từ Bước 1 vào đây
const supabaseUrl = 'https://ufqjggevnsahhfwilvkh.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmcWpnZ2V2bnNhaGhmd2lsdmtoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4MjEwMzgsImV4cCI6MjA3ODM5NzAzOH0.wSbdtofKG-VvIfJI6QZS26FB-6nH8sgmnuB71vseou4'

// Tạo ra một "cầu nối" duy nhất và "xuất" nó ra
export const supabase = createClient(supabaseUrl, supabaseAnonKey)