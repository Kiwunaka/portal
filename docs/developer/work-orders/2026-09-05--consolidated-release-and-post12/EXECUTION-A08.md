# A08 — Smart DNS / ECH boundary, 2026-09-06

**PARTIAL / I3.** Platform source commit `959d1f5`.
[Команды, точные source SHA и локальные логи](evidence/a08-ech-rejection.json).

Smart DNS parser принимал ClientHello с разрешённым внешним SNI, даже если
расширение ECH скрывало внутреннее имя. Это противоречило текущему lab contract.
Регрессия создаёт настоящий TLS 1.3 ECH ClientHello стандартной библиотекой Go
через `net.Pipe`: outer `api.openai.com`, inner `hidden.example`; соединений с
этими доменами нет. До исправления parser возвращал разрешённое outer имя.

Пять строк parser теперь отвергают ECH до origin dialing. Идентификатор
расширения сверён с [IANA](https://www.iana.org/assignments/tls-extensiontype-values/tls-extensiontype-values.xhtml).
Ограничение совместимости: ECH GREASE тоже отклоняется. Здесь нет ключа для
проверки inner имени; видимое outer имя не подтверждает application destination.
Обычный видимый SNI остаётся поддержан. Подавление DNS HTTPS/SVCB само по себе
не закрывает этот случай, поскольку ECH config может быть уже закеширован.
Canonical deployment owner и server README описывают эту границу. Старое
заявление README «не развёрнут» заменено ссылкой на exact runtime receipts:
исходники сами по себе не доказывают ни наличие, ни отсутствие deployment.

| Критерий A08 | Текущая проверка | Граница |
| --- | --- | --- |
| A / AAAA / HTTPS / SVCB | Go DoH tests: synthetic IPv4 / NODATA PASS | Source fixture; client cache и live path OPEN |
| Видимый SNI / отсутствие SNI | Go TLS parser tests PASS | Локальный TLS; application session OPEN |
| ECH с разрешённым outer SNI | FAIL до фикса, PASS после | Включая отказ ECH GREASE; rollout не выполнен |
| Smart DNS отдельно от VPN/AWG | 17 client routing tests PASS; direct DoH и selected AI/Games, остальные группы VPN | Routing JSON, не traffic proof |
| WARP / protection proof | Существующие отдельные runtime/presentation границы не менялись | Нового live WARP proof нет |
| QUIC и direct fallback | Серверный lab остаётся TCP-only | End-to-end QUIC/fallback matrix OPEN |
| Доступность ChatGPT/Game Pass | DNS/TLS success не принимается за application proof | MANUAL_OWNER_TEST |

Проверки: полный Go module PASS, `go vet` PASS, Windows host compile PASS
(бинарник не запускался); Smart DNS tooling 60 PASS; client routing 17 PASS;
infrastructure/docs 61 PASS (28 прежних deprecation warnings); policy parity
PASS; package/context/diff checks PASS. Точные команды находятся в JSON evidence.
Изменений client/Core нет.

N01/N03 dependency, весь A08 и общий релиз остаются открыты. Новый Linux bundle,
production mutation, push, merge, deploy, candidate, signing и публикация не
выполнялись. Старые live receipts не подтверждают установку этого исправления.
Retained release artifacts сохранены. Rollback — scoped revert `959d1f5`.
