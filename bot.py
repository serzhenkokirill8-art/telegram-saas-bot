import json
import os
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

USER_BOT_TOKEN = "8997320238:AAFVu5uvqlwPN1HXXP-hD7x2cuUgVjGAcgY"
ADMIN_BOT_TOKEN = "8822334377:AAF6a61_IEHNEeo8SkQ4J3Kr-buKHYwuAlw"
ADMIN_CHAT_ID = 7557898213
DATA_FILE = "data.json"

DEFAULT_DATA = {
    "tariffs": [
        {"name": "Старт", "description": "10 000 RPS", "price": "9 900 ₽/мес", "details": "Идеально для теста и малого бизнеса."},
        {"name": "Бизнес", "description": "50 000 RPS", "price": "49 000 ₽/мес", "details": "Оптимально для средних проектов."},
        {"name": "Максимум", "description": "200 000 RPS", "price": "149 000 ₽/мес", "details": "Полная мощность для энтерпрайза."},
    ],
    "tech_specs": (
        "Разработано на С++/Java/Python. "
        "Полная изоляция в Docker-контейнерах. "
        "Поддержка серверов High-CPU с частотой до 5 ГГц. "
        "Сетевой канал 1 Гбит/с с безлимитным трафиком и встроенной связью от DDoS."
    ),
    "support_username": "@Kirill5263",
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, indent=2, ensure_ascii=False)
        return DEFAULT_DATA.copy()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 НАШИ ТАРИФЫ", callback_data="tariffs")],
        [InlineKeyboardButton("⚡️Технические характеристики и Мощность", callback_data="tech_specs")],
        [InlineKeyboardButton("👨‍💻 связаться с тех.поддержкой", callback_data="support")],
    ])

def tariffs_menu_keyboard(tariffs):
    buttons = [[InlineKeyboardButton(f"{t['name']} ({t['price']})", callback_data=f"tariff_{i}")] for i, t in enumerate(tariffs)]
    return InlineKeyboardMarkup(buttons)

async def user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в сервис аренды высоконагруженных API!\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
    )

async def user_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    if query.data == "tariffs":
        if not data["tariffs"]:
            await query.edit_message_text("Тарифы пока не добавлены.")
            return
        await query.edit_message_text("Выберите тариф:", reply_markup=tariffs_menu_keyboard(data["tariffs"]))
    elif query.data == "tech_specs":
        await query.edit_message_text(data["tech_specs"], reply_markup=main_menu_keyboard())
    elif query.data == "support":
        await query.edit_message_text(f"Техподдержка: {data['support_username']}\nНапишите для связи.", reply_markup=main_menu_keyboard())
    elif query.data.startswith("tariff_"):
        idx = int(query.data.split("_")[1])
        if idx >= len(data["tariffs"]):
            await query.edit_message_text("Тариф не найден.")
            return
        tariff = data["tariffs"][idx]
        text = (
            f"<b>{tariff['name']}</b>\n"
            f"Производительность: {tariff['description']}\n"
            f"Цена: {tariff['price']}\n"
            f"Описание: {tariff['details']}\n\n"
            "Для тест-драйва нажмите кнопку ниже."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Запросить тест-драйв", callback_data=f"testdrive_{idx}")],
            [InlineKeyboardButton("« Назад", callback_data="tariffs")],
        ])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    elif query.data.startswith("testdrive_"):
        idx = int(query.data.split("_")[1])
        if idx >= len(data["tariffs"]):
            await query.answer("Ошибка.")
            return
        tariff = data["tariffs"][idx]
        user = query.from_user
        await query.edit_message_text(
            "Запрос принят. Технический специалист связывается с вами в течение нескольких минут для обеспечения производительности и передачи тестового Docker-образа."
        )
        admin_msg = (
            f"⚠️ Внимание! Пользователь @{user.username or user.id} запросил тест-драйв тарифа <b>{tariff['name']}</b> ({tariff['price']}). "
            "Срочно свяжись для обсуждения условий!"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="HTML")

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Редактировать тарифы", callback_data="admin_tariffs")],
        [InlineKeyboardButton("📝 Редактировать тех. характеристики", callback_data="admin_tech")],
        [InlineKeyboardButton("📝 Редактировать контакт поддержки", callback_data="admin_support")],
    ])
    await update.message.reply_text("Админ-панель управления контентом:", reply_markup=keyboard)

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    if query.data == "admin_tariffs":
        buttons = [[InlineKeyboardButton(f"❌ {t['name']}", callback_data=f"deltariff_{i}")] for i, t in enumerate(data["tariffs"])]
        buttons.append([InlineKeyboardButton("➕ Добавить тариф", callback_data="addtariff")])
        buttons.append([InlineKeyboardButton("« В главное меню", callback_data="admin_main")])
        await query.edit_message_text("Текущие тарифы (нажмите для удаления):", reply_markup=InlineKeyboardMarkup(buttons))
    elif query.data == "admin_tech":
        await query.edit_message_text(f"Текущие тех. характеристики:\n\n{data['tech_specs']}\n\nОтправьте новый текст для замены.")
        context.user_data["admin_action"] = "tech_specs"
    elif query.data == "admin_support":
        await query.edit_message_text(f"Текущий контакт поддержки: {data['support_username']}\nОтправьте новый username (например, @support).")
        context.user_data["admin_action"] = "support"
    elif query.data.startswith("deltariff_"):
        idx = int(query.data.split("_")[1])
        if 0 <= idx < len(data["tariffs"]):
            del data["tariffs"][idx]
            save_data(data)
            await query.answer("Тариф удалён.")
        buttons = [[InlineKeyboardButton(f"❌ {t['name']}", callback_data=f"deltariff_{i}")] for i, t in enumerate(data["tariffs"])]
        buttons.append([InlineKeyboardButton("➕ Добавить тариф", callback_data="addtariff")])
        buttons.append([InlineKeyboardButton("« В главное меню", callback_data="admin_main")])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    elif query.data == "addtariff":
        await query.edit_message_text("Введите название тарифа:")
        context.user_data["admin_action"] = "new_tariff_name"
    elif query.data == "admin_main":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Редактировать тарифы", callback_data="admin_tariffs")],
            [InlineKeyboardButton("📝 Редактировать тех. характеристики", callback_data="admin_tech")],
            [InlineKeyboardButton("📝 Редактировать контакт поддержки", callback_data="admin_support")],
        ])
        await query.edit_message_text("Админ-панель управления контентом:", reply_markup=keyboard)

async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    action = context.user_data.get("admin_action")
    if not action:
        return
    data = load_data()

    if action == "tech_specs":
        data["tech_specs"] = text
        save_data(data)
        await update.message.reply_text("Тех. характеристики обновлены.")
        context.user_data.pop("admin_action", None)
    elif action == "support":
        data["support_username"] = text
        save_data(data)
        await update.message.reply_text("Контакт поддержки обновлён.")
        context.user_data.pop("admin_action", None)
    elif action == "new_tariff_name":
        context.user_data["new_tariff"] = {"name": text}
        context.user_data["admin_action"] = "new_tariff_description"
        await update.message.reply_text("Введите описание (например, '50 000 RPS'):")
    elif action == "new_tariff_description":
        context.user_data["new_tariff"]["description"] = text
        context.user_data["admin_action"] = "new_tariff_price"
        await update.message.reply_text("Введите цену (например, '49 000 ₽/мес'):")
    elif action == "new_tariff_price":
        context.user_data["new_tariff"]["price"] = text
        context.user_data["admin_action"] = "new_tariff_details"
        await update.message.reply_text("Введите подробное описание:")
    elif action == "new_tariff_details":
        new_tariff = context.user_data.pop("new_tariff")
        new_tariff["details"] = text
        data["tariffs"].append(new_tariff)
        save_data(data)
        context.user_data.pop("admin_action", None)
        await update.message.reply_text("Тариф успешно добавлен!")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Редактировать тарифы", callback_data="admin_tariffs")],
            [InlineKeyboardButton("« В главное меню", callback_data="admin_main")],
        ])
        await update.message.reply_text("Что дальше?", reply_markup=keyboard)

async def admin_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда. Используйте кнопки.")

def start_user_bot():
    app = Application.builder().token(USER_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", user_start))
    app.add_handler(CallbackQueryHandler(user_button_handler))
    app.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

def start_admin_bot():
    app = Application.builder().token(ADMIN_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", admin_start))
    app.add_handler(CallbackQueryHandler(admin_button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_handler))
    app.add_handler(MessageHandler(filters.COMMAND, admin_unknown))
    app.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == "__main__":
    load_data()
    thread1 = threading.Thread(target=start_user_bot, daemon=True)
    thread2 = threading.Thread(target=start_admin_bot, daemon=True)
    thread1.start()
    thread2.start()
    print("Оба бота запущены в отдельных потоках. Нажмите Ctrl+C для выхода.")
    thread1.join()
    thread2.join()
