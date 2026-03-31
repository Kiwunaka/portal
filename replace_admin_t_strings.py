import os

p1 = r'C:\Users\kiwun\Documents\ai\VPN\webapp\src\app\(dashboard)\admin\broadcast\page.tsx'
p2 = r'C:\Users\kiwun\Documents\ai\VPN\webapp\src\app\(dashboard)\admin\dashboard\page.tsx'

with open(p1, 'r', encoding='utf-8') as f:
    c1 = f.read()

c1 = c1.replace('"T-3 A"', '"За 3 дня (А)"')
c1 = c1.replace('"T-3 B"', '"За 3 дня (Б)"')
c1 = c1.replace('"T-1 A"', '"За 1 день (А)"')
c1 = c1.replace('"T-1 B"', '"За 1 день (Б)"')
c1 = c1.replace('"T0 A"', '"В день окончания (А)"')
c1 = c1.replace('"T0 B"', '"В день окончания (Б)"')

with open(p1, 'w', encoding='utf-8') as f:
    f.write(c1)

with open(p2, 'r', encoding='utf-8') as f:
    c2 = f.read()

c2 = c2.replace(
    'T-3 ${summary?.retention.pings_24h.t3 ?? 0}, T-1 ${summary?.retention.pings_24h.t1 ?? 0}, T0 ${summary?.retention.pings_24h.t0 ?? 0}',
    'за 3 дня — ${summary?.retention.pings_24h.t3 ?? 0}, за 1 день — ${summary?.retention.pings_24h.t1 ?? 0}, в день окончания — ${summary?.retention.pings_24h.t0 ?? 0}'
)

with open(p2, 'w', encoding='utf-8') as f:
    f.write(c2)

print("Тексты в админке обновлены успешно!")
