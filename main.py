import logging
import sqlite3
from datetime import datetime, timedelta
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

nest_asyncio.apply()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# আপনার এডমিন টেলিগ্রাম আইডি
ADMIN_ID = 7498057677

WAITING_METHOD, WAITING_NUMBER, WAITING_AMOUNT = range(3)

def init_db():
    conn = sqlite3.connect('mining_bot_v3.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            last_claim TEXT,
            task1 INTEGER DEFAULT 0,
            task2 INTEGER DEFAULT 0,
            task3 INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_main_menu():
    keyboard = [
        [KeyboardButton("⛏️ মাইনিং"), KeyboardButton("📋 টাস্ক")],
        [KeyboardButton("💰 ব্যালেন্স"), KeyboardButton("👥 রেফার")],
        [KeyboardButton("💸 উত্তোলন"), KeyboardButton("🛠️ সাপোর্ট টিম")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('mining_bot_v3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, balance, last_claim, task1, task2, task3) 
            VALUES (?, 0, ?, 0, 0, 0)
        ''', (user_id, '2000-01-01 00:00:00'))
        conn.commit()
    conn.close()

    await update.message.reply_text(
        "স্বাগতম! 🤖 XOS EARNING Mining Bot এ আপনাকে স্বাগতম।\n\n"
        "নিচের মেনু থেকে আপনার পছন্দমতো অপশন বেছে নিন:",
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('mining_bot_v3.db')
    cursor = conn.cursor()
    
    if text == "⛏️ মাইনিং":
        cursor.execute('SELECT balance, last_claim FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        balance, last_claim_str = result if result else (0, '2000-01-01 00:00:00')
        
        last_claim_time = datetime.strptime(last_claim_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        
        if now - last_claim_time >= timedelta(hours=24):
            new_balance = balance + 100
            new_time = now.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('UPDATE users SET balance = ?, last_claim = ? WHERE user_id = ?', (new_balance, new_time, user_id))
            conn.commit()
            
            await update.message.reply_text(
                f"🎉 অভিনন্দন! আপনি সফলভাবে ১০০ পয়েন্ট ক্লেইম করেছেন!\n💰 নতুন ব্যালেন্স: {new_balance} পয়েন্ট\n\nআগামী ২৪ ঘণ্টা পর আবার ক্লেইম করতে পারবেন।",
                reply_markup=get_main_menu()
            )
        else:
            remaining = timedelta(hours=24) - (now - last_claim_time)
            hours = int(remaining.seconds // 3600)
            minutes = int((remaining.seconds % 3600) // 60)
            
            await update.message.reply_text(
                f"⏳ এখনও ২৪ ঘণ্টা পূর্ণ হয়নি!\nদয়া করে আরও {hours} ঘণ্টা {minutes} মিনিট পর আবার চেষ্টা করুন।",
                reply_markup=get_main_menu()
            )
            
    elif text == "💰 ব্যালেন্স":
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        balance = row[0] if row else 0
        await update.message.reply_text(f"💰 আপনার বর্তমান ব্যালেন্স: {balance} পয়েন্ট", reply_markup=get_main_menu())
        
    elif text == "📋 টাস্ক":
        cursor.execute('SELECT task1, task2, task3 FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        t1, t2, t3 = row if row else (0, 0, 0)
        
        t1_text = "✅ সম্পন্ন" if t1 == 1 else "👉 ফলো করুন"
        t2_text = "✅ সম্পন্ন" if t2 == 1 else "👉 জয়েন করুন"
        t3_text = "✅ সম্পন্ন" if t3 == 1 else "👉 জয়েন করুন"
        
        keyboard = [
            [InlineKeyboardButton(f"১. ফেসবুক ফলো ({t1_text})", url="https://www.facebook.com/profile.php?id=61595344414012")],
            [InlineKeyboardButton(f"২. টেলিগ্রাম চ্যানেল জয়েন ({t2_text})", url="https://t.me/EZXXOS1")],
            [InlineKeyboardButton(f"৩. মেসেজ গ্রুপ জয়েন ({t3_text})", url="https://t.me/EZXXOS")],
            [InlineKeyboardButton("🎁 টাস্ক ১ পয়েন্ট সংগ্রহ (১০)", callback_data="claim_task_1")],
            [InlineKeyboardButton("🎁 টাস্ক ২ পয়েন্ট সংগ্রহ (১০)", callback_data="claim_task_2")],
            [InlineKeyboardButton("🎁 টাস্ক ৩ পয়েন্ট সংগ্রহ (১০)", callback_data="claim_task_3")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📋 **বট টাস্ক লিস্ট**\n\n"
            "১. ফেসবুক প্রোফাইল/পেজ ফলো করুন।\n"
            "২. টেলিগ্রাম অফিশিয়াল চ্যানেলে জয়েন করুন।\n"
            "৩. টেলিগ্রাম মেসেজ গ্রুপে জয়েন করুন।\n\n"
            "কাজ সম্পন্ন করে নিচে সংশ্লিষ্ট 'পয়েন্ট সংগ্রহ' বাটনে চাপ দিয়ে ১০ পয়েন্ট করে সংগ্রহ করুন!",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    elif text == "👥 রেফার":
        bot_username = context.bot.username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        await update.message.reply_text(f"👥 আপনার রেফারেল লিংক:\n`{referral_link}`\n\nবন্ধুদের সাথে শেয়ার করে ইনকাম বাড়ান!", parse_mode="Markdown", reply_markup=get_main_menu())
        
    elif text == "🛠️ সাপোর্ট টিম":
        support_keyboard = [
            [InlineKeyboardButton("🟢 WhatsApp সাপোর্ট", url="https://wa.me/8801819579892")],
            [InlineKeyboardButton("🔵 Telegram পার্সোনাল চ্যাট", url="https://t.me/EZXXOS")]
        ]
        support_markup = InlineKeyboardMarkup(support_keyboard)
        
        await update.message.reply_text(
            "🛠️ **সাপোর্ট টিম**\n\n"
            "যেকোনো প্রয়োজনে সরাসরি আমাদের সাথে যোগাযোগ করুন:\n\n"
            "🟢 WhatsApp: `01819579892`\n"
            "🔵 Telegram: `@EZXXOS`",
            parse_mode="Markdown",
            reply_markup=support_markup
        )
        
    conn.close()
    return ConversationHandler.END

async def task_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    conn = sqlite3.connect('mining_bot_v3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance, task1, task2, task3 FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return
        
    balance, t1, t2, t3 = row
    
    if data == "claim_task_1":
        if t1 == 1:
            await query.answer("আপনি ইতিমধ্যে ফেসবুক টাস্ক সম্পন্ন করেছেন!", show_alert=True)
        else:
            new_balance = balance + 10
            cursor.execute('UPDATE users SET balance = ?, task1 = 1 WHERE user_id = ?', (new_balance, user_id))
            conn.commit()
            await query.answer("🎉 ১০ পয়েন্ট যোগ হয়েছে!", show_alert=True)
            await query.edit_message_text(text=f"✅ ফেসবুক ফলো টাস্ক সম্পন্ন হয়েছে!\n💰 নতুন ব্যালেন্স: {new_balance} পয়েন্ট")
            
    elif data == "claim_task_2":
        if t2 == 1:
            await query.answer("আপনি ইতিমধ্যে টেলিগ্রাম চ্যানেল টাস্ক সম্পন্ন করেছেন!", show_alert=True)
        else:
            new_balance = balance + 10
            cursor.execute('UPDATE users SET balance = ?, task2 = 1 WHERE user_id = ?', (new_balance, user_id))
            conn.commit()
            await query.answer("🎉 ১০ পয়েন্ট যোগ হয়েছে!", show_alert=True)
            await query.edit_message_text(text=f"✅ টেলিগ্রাম চ্যানেল জয়েন টাস্ক সম্পন্ন হয়েছে!\n💰 নতুন ব্যালেন্স: {new_balance} পয়েন্ট")
            
    elif data == "claim_task_3":
        if t3 == 1:
            await query.answer("আপনি ইতিমধ্যে মেসেজ গ্রুপ টাস্ক সম্পন্ন করেছেন!", show_alert=True)
        else:
            new_balance = balance + 10
            cursor.execute('UPDATE users SET balance = ?, task3 = 1 WHERE user_id = ?', (new_balance, user_id))
            conn.commit()
            await query.answer("🎉 ১০ পয়েন্ট যোগ হয়েছে!", show_alert=True)
            await query.edit_message_text(text=f"✅ মেসেজ গ্রুপ জয়েন টাস্ক সম্পন্ন হয়েছে!\n💰 নতুন ব্যালেন্স: {new_balance} পয়েন্ট")
            
    conn.close()

# --- Withdrawal Flow ---
async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('mining_bot_v3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    balance = row[0] if row else 0
    conn.close()

    if balance < 100:
        await update.message.reply_text(
            f"❌ আপনার পয়েন্ট পর্যাপ্ত নয়!\n\n"
            f"💰 আপনার বর্তমান ব্যালেন্স: {balance} পয়েন্ট\n"
            f"⚠️ সর্বনিম্ন উত্তোলন সীমা: ১০০ (100) পয়েন্ট।\n\n"
            f"দয়া করে টাস্ক পূরণ করে বা মাইনিং করে পয়েন্ট অর্জন করুন।",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    else:
        keyboard = [
            [InlineKeyboardButton("বিকাশ (bKash)", callback_data="method_bkash")],
            [InlineKeyboardButton("নগদ (Nagad)", callback_data="method_nagad")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💸 **উত্তোলন সার্ভিস**\n\n"
            f"💰 আপনার ব্যালেন্স: {balance} পয়েন্ট\n"
            f"⚠️ সর্বনিম্ন উত্তোলন: ১০০ পয়েন্ট\n\n"
            f"পেমেন্ট নেওয়ার জন্য নিচের যেকোনো একটি অপশন সিলেক্ট করুন:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return WAITING_METHOD

async def method_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "method_bkash":
        method_name = "বিকাশ (bKash)"
    elif data == "method_nagad":
        method_name = "নগদ (Nagad)"
    else:
        return WAITING_METHOD

    context.user_data['withdraw_method'] = method_name
    
    await query.edit_message_text(
        f"আপনি **{method_name}** সিলেক্ট করেছেন।\n\n"
        f"দয়া করে আপনার **{method_name} নম্বরটি** লিখুন:",
        parse_mode="Markdown"
    )
    return WAITING_NUMBER

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text
    context.user_data['withdraw_number'] = number
    
    await update.message.reply_text(
        f"নম্বর গ্রহণ করা হয়েছে: `{number}`\n\n"
        f"কত পয়েন্ট উত্তোলন করতে চান? (সংখ্যায় লিখুন, যেমন: 100):",
        parse_mode="Markdown"
    )
    return WAITING_AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "নাই"
    first_name = user.first_name
    
    amount_text = update.message.text
    
    if not amount_text.isdigit():
        await update.message.reply_text("❌ দয়া করে শুধুমাত্র সংখ্যা লিখুন (যেমন: 100)। আবার চেষ্টা করুন:")
        return WAITING_AMOUNT
        
    amount = int(amount_text)
    
    conn = sqlite3.connect('mining_bot_v3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    balance = row[0] if row else 0
    
    if amount < 100:
        await update.message.reply_text("❌ সর্বনিম্ন ১০০ পয়েন্ট উত্তোলন করতে পারবেন। আবার পয়েন্ট পরিমাণ লিখুন:")
        conn.close()
        return WAITING_AMOUNT
        
    if amount > balance:
        await update.message.reply_text(f"❌ আপনার ওয়ালেটে এতো পয়েন্ট নেই! আপনার ব্যালেন্স: {balance} পয়েন্ট। আবার চেষ্টা করুন:")
        conn.close()
        return WAITING_AMOUNT

    new_balance = balance - amount
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    method = context.user_data.get('withdraw_method', 'মোবাইল ব্যাংকিং')
    number = context.user_data.get('withdraw_number')
    
    # --- ইউজারকে কনফার্মেশন মেসেজ ---
    await update.message.reply_text(
        f"✅ **পেমেন্ট রিকোয়েস্ট সাবমিট হয়েছে!**\n\n"
        f"উত্তোলন মাধ্যম: {method}\n"
        f"📱 নম্বর: `{number}`\n"
        f"💎 পয়েন্ট: {amount}\n"
        f"💰 অবশিষ্ট ব্যালেন্স: {new_balance} পয়েন্ট\n\n"
        f"এডমিন পেমেন্ট যাচাই করে ২৪ ঘণ্টার মধ্যে পাঠিয়ে দেবেন। ধন্যবাদ!",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    
    # --- এডমিন আইডিতে সরাসরি নোটিফিকেশন পাঠানো ---
    try:
        admin_msg = (
            f"🚨 **নতুন পেমেন্ট রিকোয়েস্ট এসেছে!**\n\n"
            f"👤 **ইউজার:** {first_name} ({username})\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🏦 **মেথড:** {method}\n"
            f"📱 **নম্বর:** `{number}`\n"
            f"💎 **পয়েন্ট:** {amount}\n"
            f"⏰ **সময়:** {datetime.now().strftime('%Y-%m-%d %I:%M %p')}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Failed to send admin notification: {e}")

    return ConversationHandler.END

def main():
    TOKEN = "8955275739:AAEZP7iXFE7ODzztCq-EtdYAeVgv5BBxJO8"

    app = ApplicationBuilder().token(TOKEN).build()

    withdraw_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💸 উত্তোলন$"), start_withdraw)],
        states={
            WAITING_METHOD: [CallbackQueryHandler(method_callback_handler, pattern="^method_")],
            WAITING_NUMBER: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_number)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_amount)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(withdraw_handler)
    app.add_handler(CallbackQueryHandler(task_callback_handler, pattern="^claim_task_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))

    print("বট সফলভাবে চালু হচ্ছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
