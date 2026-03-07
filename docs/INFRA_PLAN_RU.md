# Infra Plan PORTAL

Обновлено: 6 марта 2026

## Текущее состояние

- control plane: `brain`
- data plane: `us`, `pl`, `it`, `free`
- текущая база пользователей небольшая, поэтому главная задача сейчас не expansion, а стабильность и наблюдаемость

## Рекомендация на сейчас

- не добавлять новые paid nodes до появления реальной нагрузки
- считать `free` node single point of failure
- держать фокус на:
  - свежести collector metrics
  - стабильности panel sync
  - мониторинге unhealthy/stale состояний

## Когда масштабировать

- sustained рост active users
- рост concurrent sessions и traffic на node
- ухудшение latency / health score
- регулярные ошибки panel sync или падение free node

## Политика отключения / расширения

- если node стабильно unhealthy или под блокировкой:
  - выключить её из выдачи
  - не удалять сразу данные пользователя
  - провести resync на рабочие nodes
- если free node нестабильна:
  - ограничить её участие только во free-сценариях
  - не смешивать с paid delivery

## Что нужно следующей волной

- показать в `/admin` stale metrics и unhealthy nodes как alert surface
- зафиксировать резервный план resync при падении node

## Canary-политика на сейчас

- Любые transport/network изменения катим не на всех сразу.
- Минимальная схема:
  - 1 нода или 1 ограниченная группа пользователей;
  - отдельный campaign/start-link;
  - сравнение support-жалоб, callback-пути, open tickets и retention-сигналов до/после.
- Stop-сигналы для отката:
  - рост open tickets;
  - рост reconnect/подключенческих жалоб;
  - деградация health score;
  - всплеск ручных обращений из конкретного региона/оператора.

## Что считаем достаточной устойчивостью

- минимум 2 здоровые рабочие ноды для paid-контура;
- `portal-node-metrics.timer` свежий;
- `/api/admin/metrics/status` = `fresh`;
- rollout делается через canary, а не одним массовым переключением.
