# R12-C05 — лицензионные тексты из заголовков выбранных исходников

Дата: 2026-09-06. **I3 / PARTIALLY_FIXED**; полный C05 открыт.
Core `8dc57a830bd1487389dd1b7c9190f094c31e13bc`; клиент до изменения
`64a26c394a8d85c79f32877f1beb1c6f7ae3939f`. Продолжение
[пакета исходников](EXECUTION-C05-SOURCE-PACKET.md) и
[вложенных notices](EXECUTION-C05-NESTED-NOTICES.md).
[Receipt и точные команды](evidence/c05-file-headers.json).

## Изменение

В общий `native-go-NOTICES.txt` добавлены 12 исходных comment blocks:
Inferno/Lucent/Vita Nuova, fiat-crypto, FreeBSD ELF, UTF-8 decoder,
quic-go tree, protobuf, Murmur, Psiphon proxy/TLS и отдельные MIT headers.
Тексты скопированы побайтно; их copyright, условия и disclaimers не правились.
Прежние 173 текста и весь предыдущий asset сохранены как неизменный prefix.
Теперь 185 текстов, 659001 bytes, SHA-256
`71b707bb4af6d879c6ce13d86644ce1e1dbd5dabb7846085b10e798d63e9b56a`.
Runtime manifest и три клиентских canonical owners обновлены.
Client commit: `7bef147c14beea9b8a45a48fedbc22f5205f7f53`.

Проверены hashes всех 6751 файлов из прежних пяти source graphs. В первых
160 строках найдены 25 разных полных permission/redistribution comment blocks.
Сравнение исходного текста после удаления comment markers и пробелов выявило
уже включённые тела; одинаковые Inferno bodies сгруппированы, вложенный proxy
текст сохранён один раз вместе со всеми source references. Это буквальное
сравнение для устранения дублей, а не вывод о совместимости лицензий.

## Проверенная упаковка

- **PASS:** четыре Direct release-mode APK содержат точный asset и все
  185 body hashes; Core SO совпадают с bound AAR. Signer — Android Debug.
- **PASS:** Windows release-mode bundle содержит 302 файла. Только notices
  отличаются от предыдущего bundle; остальные 301 файл совпали побайтно.
  Core/Cronet/OFL совпали с inputs; оба EXE имеют `NotSigned`.
- **PASS:** четыре preexisting generated registrants сохранены побайтно.
  Исходный CMake install prefix восстановлен в точное значение
  `$<TARGET_FILE_DIR:pokrov_windows>` после проверки cache.
- **PASS:** client seed/docs и staged diff checks. Staged Git blob содержит
  те же 185 body hashes. Performance collector внутри seed использует fixture,
  а не новое измерение на физическом устройстве.

Пакеты используют loopback API и сохранены отдельно в
`E:/r12-c05-header-review/`; прежние пакеты, inventory и исходники сохранены.
Первая широкая проба сканера дала лишние кандидаты и ошибку cp1251 при выводе;
она не считается успешной проверкой и сохранена отдельно. Итоговый bounded
scan завершился с exit 0. Первая попытка вернуть CMake prefix нормализовала
его в абсолютный путь; без install/build в этом состоянии выполнен configure
через штатную инициализацию, затем проверено точное исходное значение.

## Граница результата

Сканер не покрывает все поздние headers, SPDX-only references и transitive
native includes. Root license Psiphon utls, полная оценка corresponding source,
native reproduction и installed privacy остаются OPEN. Runtime source и
Core bytes не изменились; финальная candidate/device/SCM/TUN/origin приёмка
не получает PASS от сборки notices. Push, merge, deploy, production signing
и новый release candidate не выполнялись. Rollback — scoped client commit;
прежние binaries и evidence сохранены.
