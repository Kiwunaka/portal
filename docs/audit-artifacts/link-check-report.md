# Link Check Report

- Проверено файлов: 6
- FAIL: 0
- PASS: 7

| Статус | Файл | Сообщение |
| --- | --- | --- |
| PASS | `marketing\src\app\page.tsx` | Cold CTA переведены на bot-first сценарий |
| PASS | `marketing\src\app\offer\page.tsx` | Legal CTA переведён в безопасный Telegram flow |
| PASS | `marketing\src\app\privacy\page.tsx` | Legal CTA переведён в безопасный Telegram flow |
| PASS | `webapp\src\app\(dashboard)\support\legal\page.tsx` | Юридические ссылки webapp указывают на marketing absolute URL |
| PASS | `portal_bot\api.py` | Admin campaign link builder переводит public checkout в safe fallback |
| PASS | `portal_bot\api.py` | Compat env-flag для numeric subscription fallback подключён |
| PASS | `marketing\src\app\checkout\page.tsx` | Checkout heading визуально разделён корректно |
