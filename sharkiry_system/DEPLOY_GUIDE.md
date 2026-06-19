# วิธีรัน & Deploy ระบบ Sharkiry OMS

## รันในเครื่อง (Local)

### ขั้นตอนที่ 1 — ติดตั้ง Python packages
```bash
pip install flask gunicorn
```

### ขั้นตอนที่ 2 — รันระบบ
```bash
cd sharkiry_system
python app.py
```
เปิด browser ไปที่ **http://127.0.0.1:5000**

### บัญชีผู้ใช้
| Username | Password     | สิทธิ์              |
|----------|--------------|---------------------|
| admin    | sharkiry2026 | เต็ม (ทุกหน้า)     |
| marcom   | sharkiry2026 | MarCom (Reports)    |
| staff    | staff1234    | Staff (Orders/Stock) |

---

## Deploy บน Render.com (ฟรี)

### ขั้นตอนที่ 1 — Push โค้ดขึ้น GitHub
1. สร้าง repository ใหม่บน [github.com](https://github.com)
2. อัปโหลดโฟลเดอร์ `sharkiry_system` ทั้งหมด

```bash
git init
git add .
git commit -m "Sharkiry OMS v1"
git remote add origin https://github.com/YOUR_USERNAME/sharkiry-oms.git
git push -u origin main
```

### ขั้นตอนที่ 2 — สร้าง Web Service บน Render
1. ไปที่ [render.com](https://render.com) → **New → Web Service**
2. เลือก GitHub repo ที่สร้างไว้
3. กรอก settings:
   - **Name**: sharkiry-oms
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

### ขั้นตอนที่ 3 — ตั้ง Environment Variable
ใน Render dashboard → **Environment**:
```
SECRET_KEY = sharkiry-secret-2026-xxx
```

### ขั้นตอนที่ 4 — Deploy
กด **Create Web Service** รอประมาณ 2-3 นาที
ได้ URL เช่น `https://sharkiry-oms.onrender.com`

> **หมายเหตุ:** Render Free tier จะ sleep หลังจากไม่มีการใช้งาน 15 นาที
> ครั้งแรกที่เปิดจะช้าประมาณ 30-60 วินาที (wake up)
> แก้ได้โดย upgrade เป็น Starter plan ($7/เดือน)

---

## โครงสร้างไฟล์
```
sharkiry_system/
├── app.py              ← Flask app หลัก + routes ทั้งหมด
├── requirements.txt    ← flask, gunicorn
├── Procfile            ← สำหรับ Render/Heroku
├── sharkiry.db         ← SQLite database (สร้างอัตโนมัติ)
└── templates/
    ├── base.html           ← Layout + sidebar + CSS ทั้งหมด
    ├── login.html          ← หน้า Login
    ├── dashboard.html      ← Dashboard KPI
    ├── orders.html         ← รายการออเดอร์
    ├── order_new.html      ← สร้างออเดอร์ใหม่
    ├── order_detail.html   ← รายละเอียดออเดอร์
    ├── customers.html      ← รายชื่อลูกค้า
    ├── customer_detail.html ← ประวัติลูกค้า
    ├── inventory.html      ← สต็อกสินค้า
    ├── leads.html          ← Lead Kanban
    └── reports.html        ← รายงานยอดขาย
```

---

## ฟีเจอร์ที่มีใน v1

- **Dashboard** — KPI วันนี้, แผนภูมิรายได้ 6 เดือน, สต็อกต่ำ
- **Orders** — สร้าง/จัดการออเดอร์ทุกช่องทาง (Line/FB/IG/TikTok/Shopee/เว็บ)
- **Customers** — โปรไฟล์ลูกค้า, ตรวจจับลูกค้า Churn (>45 วัน)
- **Inventory** — จัดการสต็อก, ประวัติการเคลื่อนไหว
- **Leads** — Kanban board ติดตาม Lead
- **Reports** — ยอดขายแยกช่องทาง, สินค้าขายดี, แคมเปญ ROAS

## Phase 2 (ถัดไป)
- API integration กับ Shopee Open Platform
- API integration กับ TikTok Shop Open Platform
- Auto-sync orders จากทั้ง 2 แพลตฟอร์มทุก 30 นาที
