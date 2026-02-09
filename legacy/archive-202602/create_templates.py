import os
import paramiko

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, username=username, password=password, timeout=30)

print("=== CREATING DEFAULT TEMPLATES ===\n")

templates = [
    ("welcome", "👋 *Добро пожаловать!*\n\nТы успешно подключился к нашему сервису. Если нужна помощь — пиши /support"),
    ("update", "🔔 *Важное обновление!*\n\nМы обновили сервер. Если возникли проблемы — перезапусти приложение."),
    ("promo", "🎁 *Специальное предложение!*\n\nИспользуй промокод для бонусов!\n\nПодробности в боте."),
    ("expiring", "⚠️ *Подписка заканчивается!*\n\nОсталось несколько дней. Продли сейчас, чтобы не потерять доступ!"),
    ("holiday", "🎄 *С праздником!*\n\nПоздравляем с праздниками! Желаем стабильного интернета! 🎉"),
]

for key, text in templates:
    # Escape single quotes for SQL
    safe_text = text.replace("'", "''")
    sql = f"INSERT OR IGNORE INTO templates (key, text) VALUES ('{key}', '{safe_text}');"
    cmd = f'sqlite3 /root/portal_bot/portal.db "{sql}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.read().decode()
    if err:
        print(f"[FAIL] {key}: {err}")
    else:
        print(f"[OK] {key}")

print("\n[DONE] Default templates created!")
client.close()
