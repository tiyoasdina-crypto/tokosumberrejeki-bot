from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import sqlite3
from datetime import datetime

TOKEN = "8817722422:AAFrEXnhfxSkPBso32ZBthFUyAYuadCCV5w"
NAMA_TOKO = "Toko Sumberrejeki"

# Database
conn = sqlite3.connect("kasir.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS barang (
    nama TEXT PRIMARY KEY,
    harga_beli INTEGER,
    harga_jual INTEGER,
    stok INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barang TEXT,
    qty INTEGER,
    total INTEGER,
    tanggal TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS hutang (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    jumlah INTEGER,
    tanggal TEXT
)
""")

conn.commit()

menu = ReplyKeyboardMarkup(
    [
        ["🛒 Jual", "📦 Stok"],
        ["➕ Barang", "💳 Hutang"],
        ["📊 Laporan"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = f"""
🏪 {NAMA_TOKO}

Kasir Aktif ✅

Perintah:

/tambahbarang nama harga_beli harga_jual stok

Contoh:
 /tambahbarang gula 14000 16000 20

/jual nama qty
Contoh:
 /jual gula 2

/stok

/hutang nama jumlah
Contoh:
 /hutang budi 25000

/laporan
"""
    await update.message.reply_text(
        teks,
        reply_markup=menu
    )

async def tambahbarang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        nama = context.args[0].lower()
        beli = int(context.args[1])
        jual = int(context.args[2])
        stok = int(context.args[3])

        c.execute(
            "INSERT OR REPLACE INTO barang VALUES (?, ?, ?, ?)",
            (nama, beli, jual, stok)
        )
        conn.commit()

        await update.message.reply_text(
            f"✅ Barang {nama} disimpan"
        )

    except:
        await update.message.reply_text(
            "Contoh:\n/tambahbarang gula 14000 16000 20"
        )

async def stok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = c.execute(
        "SELECT * FROM barang"
    ).fetchall()

    if not data:
        await update.message.reply_text("Barang kosong")
        return

    teks = "📦 STOK BARANG\n\n"

    for b in data:
        teks += (
            f"{b[0]} | stok: {b[3]} | jual: Rp{b[2]}\n"
        )

    await update.message.reply_text(teks)

async def jual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        nama = context.args[0].lower()
        qty = int(context.args[1])

        barang = c.execute(
            "SELECT harga_jual, stok FROM barang WHERE nama=?",
            (nama,)
        ).fetchone()

        if not barang:
            await update.message.reply_text(
                "Barang tidak ditemukan"
            )
            return

        harga, stok = barang

        if stok < qty:
            await update.message.reply_text(
                "Stok tidak cukup"
            )
            return

        total = harga * qty
        stok_baru = stok - qty

        c.execute(
            "UPDATE barang SET stok=? WHERE nama=?",
            (stok_baru, nama)
        )

        c.execute(
            """INSERT INTO transaksi
            (barang, qty, total, tanggal)
            VALUES (?, ?, ?, ?)""",
            (
                nama,
                qty,
                total,
                datetime.now().strftime("%Y-%m-%d")
            )
        )

        conn.commit()

        await update.message.reply_text(
            f"""🧾 TRANSAKSI

Barang: {nama}
Qty: {qty}
Total: Rp{total}
"""
        )

    except:
        await update.message.reply_text(
            "Contoh:\n/jual gula 2"
        )

async def hutang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        nama = context.args[0]
        jumlah = int(context.args[1])

        c.execute(
            "INSERT INTO hutang (nama, jumlah, tanggal) VALUES (?, ?, ?)",
            (
                nama,
                jumlah,
                datetime.now().strftime("%Y-%m-%d")
            )
        )

        conn.commit()

        await update.message.reply_text(
            f"💳 Hutang {nama} Rp{jumlah} tersimpan"
        )

    except:
        await update.message.reply_text(
            "Contoh:\n/hutang budi 25000"
        )

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hari_ini = datetime.now().strftime("%Y-%m-%d")

    total = c.execute(
        "SELECT SUM(total) FROM transaksi WHERE tanggal=?",
        (hari_ini,)
    ).fetchone()[0]

    jumlah = c.execute(
        "SELECT COUNT(*) FROM transaksi WHERE tanggal=?",
        (hari_ini,)
    ).fetchone()[0]

    total = total if total else 0

    await update.message.reply_text(
        f"""📊 LAPORAN HARI INI

Omzet: Rp{total}
Transaksi: {jumlah}
"""
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tambahbarang", tambahbarang))
app.add_handler(CommandHandler("stok", stok))
app.add_handler(CommandHandler("jual", jual))
app.add_handler(CommandHandler("hutang", hutang))
app.add_handler(CommandHandler("laporan", laporan))

print(f"{NAMA_TOKO} aktif...")
app.run_polling()
