import os, re, json

files = [
    r'webapp/src/app/(dashboard)/admin/dashboard/page.tsx',
    r'webapp/src/app/(dashboard)/admin/nodes/page.tsx',
    r'webapp/src/app/(dashboard)/admin/promos/page.tsx',
    r'webapp/src/app/(dashboard)/admin/tickets/page.tsx',
    r'webapp/src/app/(dashboard)/admin/users/page.tsx',
    r'webapp/src/app/(dashboard)/admin/layout.tsx',
    r'webapp/src/app/(dashboard)/admin/nav.ts',
    r'webapp/src/app/(dashboard)/admin/page.tsx',
    r'webapp/src/app/(dashboard)/dashboard/downloads/page.tsx',
    r'webapp/src/app/(dashboard)/dashboard/page.tsx',
    r'webapp/src/app/(dashboard)/devices/page.tsx',
    r'webapp/src/app/(dashboard)/statistics/page.tsx',
    r'webapp/src/app/(dashboard)/subscription/checkout/page.tsx',
    r'webapp/src/app/(dashboard)/subscription/page.tsx',
    r'webapp/src/app/(dashboard)/support/legal/page.tsx',
    r'webapp/src/app/(dashboard)/support/thread/page.tsx',
    r'webapp/src/app/(dashboard)/support/page.tsx',
    r'webapp/src/app/(dashboard)/layout.tsx',
    r'webapp/src/app/pricing/page.tsx',
    r'webapp/src/app/layout.tsx',
    r'webapp/src/app/loading.tsx',
    r'webapp/src/app/qa-overlay.tsx',
    r'webapp/src/components/subscription-qr-card.tsx',
    r'webapp/src/components/telegram-login-widget.tsx',
    r'webapp/src/lib/pricing.ts',
    r'webapp/src/lib/session.tsx',
    r'webapp/src/lib\telegram-oidc.ts',
    r'marketing/src/app/bystryy-vpn-na-telefon/page.tsx',
    r'marketing/src/app/checkout/checkout-client.tsx',
    r'marketing/src/app/offer/page.tsx',
    r'marketing/src/app/privacy/page.tsx',
    r'marketing/src/app/vpn-dlya-tiktok/page.tsx',
    r'marketing/src/app/vpn-dlya-youtube/page.tsx',
    r'marketing/src/app/vpn-na-iphone-android-windows/page.tsx',
    r'marketing/src/app/vpn-telegram-bot/page.tsx',
    r'marketing/src/app/layout.tsx',
    r'marketing/src/app/page.tsx',
    r'portal_bot/api.py',
    r'portal_bot/bot.py',
    r'portal_bot/feedbackbot.py',
    r'portal_bot/gift_cards_service.py',
    r'portal_bot/helpbot.py',
    r'portal_bot/migrations.py',
    r'portal_bot/payment_providers.py',
    r'portal_bot/worker.py'
]

results = {}
russian_pattern = re.compile(r'[\"\'\`>]([^\"\'\`<>]*[А-Яа-яЁё][^\"\'\`<>]*)[\"\'\`<]')

for fname in files:
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple text extraction
            matches = russian_pattern.findall(content)
            found = set()
            for m in matches:
                text = m.strip()
                if text and len(text) > 1:
                    found.add(text)
            if found:
                results[fname] = list(found)
    except FileNotFoundError:
        pass

with open('russian_texts.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Analyzed texts and wrote to russian_texts.json")
