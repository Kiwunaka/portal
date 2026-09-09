# POKROV observability support reference

Generated from `error-catalog.json`; do not edit by hand.

- catalog version: `1.2.0`
- catalog SHA-256: `1cef07aea2f859891794546569431d0e6aab91c6921729389fd63013f3002af1`
- entries: `127`

Regenerate with:

```powershell
python scripts/generate_observability_support_reference.py --write
```

| Code | Severity | Owner | Safe user message (RU) | Operator action | Release blocking |
| --- | --- | --- | --- | --- | --- |
| `AND-BG-001` | warn | android | Android остановил приложение в фоне. | `show_android_background_guidance` | no |
| `AND-BG-002` | error | android | Фоновая VPN-служба настроена некорректно. | `block_unstable_android_service` | yes |
| `AND-BG-003` | warn | android | Энергосбережение Android ограничивает переподключение. | `show_android_power_guidance` | no |
| `AND-UPD-001` | warn | android | Android запрещает установку обновления из приложения. | `request_direct_install_permission` | no |
| `AND-UPD-002` | fatal | android | Проверка подлинности обновления не пройдена. | `block_android_installer` | yes |
| `AND-VPN-001` | warn | android | Android ожидает подтверждение VPN-подключения. | `request_android_vpn_consent` | no |
| `AND-VPN-002` | error | android | Android не запустил VPN-службу. | `inspect_android_service_lifecycle` | no |
| `AND-VPN-003` | error | android | Android не создал системный VPN-интерфейс. | `stop_android_vpn_service` | no |
| `AND-VPN-004` | warn | android | Разрешение VPN было отозвано системой. | `stop_after_android_permission_revoke` | no |
| `AND-VPN-005` | warn | android | Системный режим Android конфликтует с подключением. | `open_android_vpn_settings` | no |
| `API-001` | warn | network | Сервис временно недоступен из-за сетевой ошибки. | `retry_control_plane_lookup` | no |
| `API-002` | warn | network | Сервис не ответил вовремя. | `retry_control_plane_connect` | no |
| `API-003` | error | security | Защищённое соединение с сервисом не подтверждено. | `inspect_clock_and_interception` | no |
| `API-004` | warn | portal | Авторизация истекла. Войдите снова. | `request_reauthentication` | no |
| `API-005` | warn | portal | Операция запрещена текущей политикой доступа. | `stop_automatic_retry` | no |
| `API-006` | warn | portal | Слишком много запросов. Повторите позже. | `honor_retry_window` | no |
| `API-007` | warn | portal | Сервис временно недоступен. | `correlate_service_incident` | no |
| `API-008` | error | portal | Сервис вернул несовместимый ответ. | `reject_invalid_response` | no |
| `API-009` | error | release | Версия протокола не поддерживается. | `update_or_rollback_release` | yes |
| `API-010` | warn | portal | Ответ сервиса получен не полностью. | `stop_response_parsing` | no |
| `API-011` | info | portal | Параметры подключения ещё готовятся. | `wait_for_profile_provisioning` | no |
| `APP-BOOT-001` | fatal | release | Файлы выпуска отсутствуют. Требуется восстановление приложения. | `repair_release` | yes |
| `APP-BOOT-002` | fatal | release | Проверка целостности выпуска не пройдена. | `block_runtime_and_alert` | yes |
| `APP-BOOT-003` | error | app | Версия приложения несовместима с текущим контрактом. | `update_client_contract` | no |
| `APP-BOOT-004` | error | app | Не удалось безопасно обновить локальные данные. | `rollback_local_migration` | no |
| `APP-BOOT-005` | warn | app | Приложение уже запущено, но не приняло команду. | `forward_primary_instance` | no |
| `APP-BOOT-006` | warn | runtime | Обнаружено незавершённое восстановление сети. | `complete_startup_recovery` | no |
| `APP-BOOT-007` | error | app | Защищённое хранилище недоступно. | `restore_secure_storage` | no |
| `APP-BOOT-008` | error | app | Локальное состояние повреждено и требует восстановления. | `restore_state_backup` | no |
| `AUTH-001` | info | portal | Для продолжения требуется войти в аккаунт. | `request_login` | no |
| `AUTH-002` | warn | portal | Сессия завершена. Войдите снова. | `clear_session_and_reauthenticate` | no |
| `AUTH-003` | warn | app | Проверьте дату и время на устройстве. | `request_automatic_time` | no |
| `AUTH-004` | warn | portal | Достигнут лимит подключённых устройств. | `open_device_management` | no |
| `AUTH-005` | error | portal | Доступ аккаунта ограничен. Обратитесь в поддержку. | `open_support_case` | no |
| `AUTH-006` | warn | portal | Ссылка входа недействительна. Запросите новую. | `request_new_activation` | no |
| `CONN-001` | warn | app | Системное разрешение на подключение не выдано. | `show_permission_rationale` | no |
| `CONN-002` | info | app | Подключение отменено пользователем. | `record_user_cancellation` | no |
| `CONN-003` | warn | network | Нет доступной сети. Ожидаем восстановление связи. | `wait_for_network_callback` | no |
| `CONN-004` | warn | network | Сеть может требовать дополнительной авторизации. | `show_captive_portal_guidance` | no |
| `CONN-005` | error | runtime | Параметры подключения отклонены проверкой. | `reject_runtime_profile` | no |
| `CONN-006` | warn | node | Выбранная точка временно недоступна. | `select_next_node` | no |
| `CONN-007` | info | runtime | Предыдущая попытка заменена новой командой. | `discard_stale_attempt` | no |
| `CONN-008` | warn | runtime | Работа подключения не подтверждена вовремя. | `mark_connection_unverified` | no |
| `CORE-001` | fatal | core | Компонент подключения отсутствует. | `repair_core_artifact` | yes |
| `CORE-002` | fatal | core | Компонент подключения несовместим с приложением. | `block_incompatible_core` | yes |
| `CORE-003` | error | core | Компонент подключения не запустился вовремя. | `terminate_and_retry_core_once` | no |
| `CORE-004` | error | core | Компонент подключения аварийно завершился. | `rollback_after_core_crash` | no |
| `CORE-005` | error | core | Компонент подключения отклонил параметры запуска. | `show_safe_core_reason` | no |
| `CORE-006` | warn | core | Не удалось установить защищённый транспорт. | `classify_transport_failure` | no |
| `CORE-007` | error | core | Компонент подключения неожиданно остановился. | `apply_recovery_policy` | no |
| `CORE-008` | error | core | Компонент подключения не подтвердил остановку. | `force_stop_and_rollback` | no |
| `CORE-009` | error | runtime | Системный модуль не завершил действие. | `inspect_runtime_failure` | no |
| `CRASH-001` | error | app | Интерфейс приложения аварийно завершил операцию. | `capture_safe_app_signature` | no |
| `CRASH-002` | error | platform | Системный компонент приложения аварийно завершился. | `capture_safe_host_signature` | no |
| `CRASH-003` | fatal | platform | Системная служба аварийно завершилась. | `rollback_and_recover_service` | yes |
| `DNS-001` | error | platform | Не удалось применить безопасные параметры DNS. | `rollback_dns_transaction` | no |
| `DNS-002` | error | runtime | Работа DNS через подключение не подтверждена. | `mark_dns_unverified` | no |
| `DNS-003` | fatal | runtime | Обнаружен риск обхода защищённого DNS. | `stop_on_dns_leak` | yes |
| `DNS-004` | fatal | platform | Исходные параметры DNS восстановлены не полностью. | `repair_dns_from_journal` | yes |
| `EGRESS-001` | error | runtime | Выход трафика через защищённый путь не подтверждён. | `keep_egress_unverified` | no |
| `EGRESS-002` | error | runtime | Подтверждённый сетевой путь не соответствует выбранному. | `stop_or_rotate_node` | no |
| `EGRESS-003` | warn | portal | Проверка сетевого пути вернула некорректный ответ. | `retry_alternate_probe` | no |
| `ENT-001` | info | portal | Для подключения нужен активный доступ. | `open_access_flow` | no |
| `ENT-002` | warn | portal | Срок доступа завершился во время подключения. | `stop_paid_connection` | no |
| `ENT-003` | warn | portal | Статус доступа обновляется. | `reconcile_entitlement` | no |
| `ENT-004` | info | portal | Награда уже была начислена ранее. | `show_existing_reward` | no |
| `HANG-001` | error | app | Интерфейс приложения временно не отвечал. | `capture_safe_ui_hang` | no |
| `HANG-002` | error | android | Android обнаружил длительную остановку приложения. | `capture_safe_android_hang` | no |
| `HANG-003` | error | platform | Системная команда не завершилась вовремя. | `cancel_timed_out_service_command` | no |
| `LNX-DNS-001` | error | linux | Linux не применил параметры DNS. | `rollback_linux_dns` | no |
| `LNX-IPC-001` | error | linux | Приложение не связалось с системной службой. | `inspect_linux_ipc` | no |
| `LNX-NFT-001` | error | linux | Linux не применил сетевые правила. | `rollback_linux_firewall` | no |
| `LNX-NFT-002` | fatal | linux | Исходные сетевые правила Linux не восстановлены. | `run_linux_firewall_recovery` | yes |
| `LNX-NM-001` | error | linux | Сетевая служба Linux конфликтует с подключением. | `rollback_linux_network_manager` | no |
| `LNX-POLKIT-001` | warn | linux | Системная политика не разрешила операцию. | `show_polkit_rationale` | no |
| `LNX-SVC-001` | error | linux | Системная служба POKROV недоступна. | `repair_linux_daemon` | no |
| `LNX-SVC-002` | fatal | linux | Версии приложения и системной службы несовместимы. | `repair_atomic_linux_install` | yes |
| `PERF-001` | warn | runtime | Один из этапов подключения выполняется слишком долго. | `record_slow_connection_phase` | no |
| `PERF-002` | warn | app | Приложение использует больше ресурсов, чем ожидалось. | `record_resource_growth` | no |
| `PERF-003` | warn | app | Фоновая нагрузка приложения выше допустимой. | `throttle_background_work` | no |
| `RECON-001` | error | runtime | Лимит повторных подключений исчерпан. | `stop_reconnect_loop` | no |
| `RECON-002` | warn | network | Сеть слишком часто меняет состояние. | `debounce_network_changes` | no |
| `RECON-003` | fatal | runtime | Безопасное восстановление сети не гарантировано. | `block_non_idempotent_recovery` | yes |
| `ROUTE-001` | error | platform | Не удалось применить сетевые маршруты. | `rollback_route_transaction` | no |
| `ROUTE-002` | fatal | platform | Исходные сетевые маршруты восстановлены не полностью. | `run_startup_route_recovery` | yes |
| `ROUTE-003` | warn | platform | Обнаружен конфликт сетевых маршрутов. | `apply_deterministic_route_policy` | no |
| `ROUTE-004` | error | runtime | Выбранный режим сети не поддерживается. | `reject_unsupported_route_mode` | no |
| `ROUTE-005` | warn | platform | Не удалось определить сетевой интерфейс устройства. | `refresh_network_interface` | no |
| `SEC-001` | fatal | security | Событие отклонено проверкой приватности. | `drop_forbidden_event` | yes |
| `SEC-002` | fatal | security | Целостность диагностических данных не подтверждена. | `block_untrusted_diagnostics` | yes |
| `SEC-003` | fatal | security | Обнаружено нарушение целостности приложения. | `block_privileged_operation` | yes |
| `SEC-004` | error | security | Политика расширенной диагностики недействительна. | `reject_remote_support_policy` | no |
| `SUP-001` | error | support | Не удалось собрать диагностический пакет. | `offer_safe_summary` | no |
| `SUP-002` | fatal | security | Проверка приватности диагностического пакета не пройдена. | `block_bundle_export` | yes |
| `SUP-003` | fatal | security | Не удалось безопасно зашифровать диагностический пакет. | `block_plaintext_bundle` | yes |
| `SUP-004` | warn | support | Разрешение на отправку диагностики истекло. | `request_new_upload_ticket` | no |
| `SUP-005` | warn | support | Отправка диагностики была прервана. | `resume_support_upload` | no |
| `SUP-006` | warn | support | Диагностика не была привязана к обращению. | `preserve_local_bundle_identity` | no |
| `TRANSPORT-001` | warn | network | Точка подключения не ответила вовремя. | `retry_transport_timeout` | no |
| `TRANSPORT-002` | warn | node | Точка подключения отклонила соединение. | `rotate_refused_endpoint` | no |
| `TRANSPORT-003` | error | node | Точка подключения отклонила проверку доступа. | `inspect_node_credentials` | no |
| `TRANSPORT-004` | error | core | Согласование протокола подключения не удалось. | `inspect_transport_compatibility` | no |
| `TRANSPORT-005` | warn | network | Ответ по UDP не получен вовремя. Причина не установлена. | `retry_udp_timeout` | no |
| `TRANSPORT-006` | warn | network | Согласование TLS не завершилось вовремя. Причина не установлена. | `retry_tls_timeout` | no |
| `TRANSPORT-007` | warn | network | Ответ после установки соединения не получен вовремя. Причина не установлена. | `retry_response_timeout` | no |
| `TUN-001` | error | platform | Не удалось создать системный VPN-интерфейс. | `inspect_tun_prerequisites` | no |
| `TUN-002` | error | platform | VPN-интерфейс не подтверждён после запуска. | `cleanup_false_green_tun` | yes |
| `TUN-003` | warn | runtime | Сеть отклонила выбранный размер пакета. | `apply_safe_mtu_fallback` | no |
| `TUN-004` | warn | runtime | Передача данных через VPN не подтверждена. | `keep_connection_unverified` | no |
| `UPD-001` | fatal | release | Манифест обновления не прошёл проверку. | `hide_invalid_update` | yes |
| `UPD-002` | fatal | release | Загруженное обновление повреждено. | `delete_invalid_update_artifact` | yes |
| `UPD-003` | fatal | release | Подлинность обновления не подтверждена. | `block_untrusted_update` | yes |
| `UPD-004` | fatal | release | Обновление предназначено для другого приложения. | `block_identity_mismatch` | yes |
| `UPD-005` | error | platform | Установщик не завершил обновление. | `preserve_previous_version` | no |
| `UPD-006` | error | release | Новая версия не прошла проверку работоспособности. | `pause_rollout_and_rollback` | yes |
| `UPD-007` | error | app | Состояние обновления требует восстановления. | `recover_update_transaction` | no |
| `WIN-DNS-001` | error | windows | Windows не применила параметры DNS. | `rollback_windows_dns` | no |
| `WIN-DNS-002` | fatal | windows | Исходные параметры DNS Windows не восстановлены. | `repair_windows_dns_from_journal` | yes |
| `WIN-SVC-001` | error | windows | Системная служба POKROV не установлена. | `repair_windows_service` | no |
| `WIN-SVC-002` | error | windows | Приложение не получило доступ к системной службе. | `inspect_windows_service_acl` | no |
| `WIN-SVC-003` | error | windows | Системная служба POKROV не отвечает. | `restart_windows_service` | no |
| `WIN-SVC-004` | fatal | windows | Версии приложения и системной службы несовместимы. | `repair_atomic_windows_install` | yes |
| `WIN-SVC-005` | error | windows | Системная служба повторно аварийно завершается. | `stop_service_restart_loop` | no |
| `WIN-SVC-006` | warn | windows | Получен ответ от устаревшей попытки подключения. | `discard_stale_ipc_response` | no |
| `WIN-TUN-001` | error | windows | Системный VPN-драйвер отсутствует. | `repair_signed_windows_driver` | no |
| `WIN-TUN-002` | error | windows | Системный VPN-драйвер не запустился. | `inspect_windows_driver_load` | no |
| `WIN-TUN-003` | warn | windows | Другое сетевое приложение мешает подключению. | `show_windows_network_conflict` | no |
