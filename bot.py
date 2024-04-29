import logging
import json
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes
from parameters import TOKEN, CHAT_ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Загрузка задач из файла JSON
def load_tasks():
    try:
        with open("tasks.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Сохранение задач в файл JSON
def save_tasks(tasks):
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=4)


# Команда добавления задачи
async def add_task(update: Update, context: CallbackContext):
    try:
        task = context.args[0]
        due_date = datetime.datetime.strptime(context.args[1], "%Y-%m-%d").date()
        tasks = load_tasks()
        tasks[task] = str(due_date)
        save_tasks(tasks)
        await update.message.reply_text(f"Задача '{task}' добвалена на {due_date}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /add <имя_задачи> <дата YYYY-MM-DD>")


# Команда удаления задачи
async def delete_task(update: Update, context: CallbackContext):
    try:
        task_to_delete = context.args[0]
        due_date_to_delete = datetime.datetime.strptime(context.args[1], "%Y-%m-%d").date()
        tasks = load_tasks()

        # Проверка существует ли задача с указанным сроком выполнения
        if task_to_delete in tasks and tasks[task_to_delete] == str(due_date_to_delete):
            del tasks[task_to_delete]
            save_tasks(tasks)
            await update.message.reply_text(f"Задача '{task_to_delete}' на {due_date_to_delete} удалена.")
        else:
            await update.message.reply_text(f"Задачи с именем '{task_to_delete}' не найдено на {due_date_to_delete}.")

    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /delete <имя_задачи> <дата YYYY-MM-DD>")


# Команда перечислить все задачи
async def list_tasks(update: Update, context: CallbackContext):
    tasks = load_tasks()
    message = "Все задачи:\n"

    if tasks:
        for task, due_date in tasks.items():
            message += f"- {task}: на {due_date}\n"
    else:
        message += "Нет задач."

    await update.message.reply_text(message)


# Работа с ежедневными напоминаниями
async def daily_reminder(context: CallbackContext):
    tasks = load_tasks()
    today = datetime.date.today()
    message = "Напоминание о задачах:\n"
    has_task = False

    for task, due_date in list(tasks.items()):
        due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
        if due_date < today:
            del tasks[task]  # Удаление прошлых задач
        else:
            message += f"- {task}: на {due_date}\n"
            has_task = True

    save_tasks(tasks)

    if has_task:
        # Доступ к chat_id из контекста задания
        chat_id = context.job.chat_id
        await context.bot.send_message(chat_id=chat_id, text=message)
        logging.info("Ежедневное напоминание отправлено")
    else:
        logging.info("Ежедневное напоминание НЕ отправлено")


# Команда старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
        Привет! Я бот-напоминалка. Я могу помочь вам вспомнить о ваших задачах.
        Команды:
        /add <имя_задачи> <дата YYYY-MM-DD>
        /delete <имя_задачи> <дата YYYY-MM-DD>
        /list (выдаёт список всех задач)

        Пример:
        /add Сдать проект 2024-01-01
        /delete Сдать проект 2024-01-01

        Бот будет ежедневно присылать вам напоминания о ваших задачах.
        """

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


if __name__ == '__main__':
    token = TOKEN
    application = ApplicationBuilder().token(token).build()

    # Обработчики
    start_handler = CommandHandler('start', start)
    add_task_handler = CommandHandler('add', add_task)
    delete_task_handler = CommandHandler('delete', delete_task)
    list_tasks_handler = CommandHandler('list', list_tasks)

    # Добавление обработчиков в приложение
    application.add_handler(start_handler)
    application.add_handler(add_task_handler)
    application.add_handler(delete_task_handler)
    application.add_handler(list_tasks_handler)

    # Добавление задач с ежедневным напоминанием
    job_queue = application.job_queue
    chat_id = CHAT_ID
    job_queue.run_daily(daily_reminder, time=datetime.time(hour=8), chat_id=chat_id)

    application.run_polling()
