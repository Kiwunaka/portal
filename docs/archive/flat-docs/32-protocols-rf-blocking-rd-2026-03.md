# Протоколы, панель и модель эксплуатации (2026-03)

Обновлено: 7 марта 2026

## 1. Текущее продуктовое решение

- В текущем production-стеке оставляем только один delivery-профиль:
  - `VLESS + TCP + Reality`
- Встроенный subscription server `3x-ui` не используем.
- Пользовательскую подписку, бизнес-логику, бонусы, платежи и выдачу ссылок продолжает собирать сам PORTAL.

## 2. Что реально стоит на серверах

- На нодах используется `3x-ui + xray-core`.
- На проверенных нодах `brain`, `pl`, `it`, `us` активен `x-ui`, а `xray-core` имеет версию `26.1.31`.
- Все стандартные production-inbounds, которые используются как базовый профиль, сейчас `vless / tcp / reality / 443`.
- На `brain` built-in sub server `x-ui` отключён (`subEnable=false`) и вынесен с `2096` на `2097`, потому что `:2096` занят portal subscription endpoint.

## 3. Насколько плохо, что у нас 3x-ui, а не direct core

Короткий ответ: для текущего масштаба это не плохо и не аварийно. Это нормальный компромисс, но с понятными ограничениями.

### 3.1 Что хорошего в 3x-ui

- быстро поднимать и обслуживать ноды;
- удобно смотреть inbounds и клиентов руками;
- меньше порог входа для оператора, чем у полностью direct-Xray конфигов;
- для текущего single-protocol стека `VLESS/TCP/Reality` хорошо совместим с нашей интеграцией через `control_panel.py`.

### 3.2 Что в 3x-ui слабее, чем у direct core

- panel state легче увести в drift ручными правками;
- есть скрытые дефолты, вроде built-in subscription service на `2096`, которые нужно отдельно отключать;
- панель сама по себе не должна быть источником истины для продукта;
- уникальность клиентов и часть ограничений определяются панельной моделью, а не нашей доменной моделью.

### 3.3 Практический вывод для PORTAL

При нынешнем масштабе правильная схема такая:
- `PORTAL` остаётся source of truth;
- `3x-ui` остаётся operational control-plane для xray;
- все продуктовые контракты держим в наших коде, БД и доках, а не в логике панели.

То есть проблема не в том, что у нас есть `3x-ui`, а в том, чтобы не позволять ей быть главным владельцем состояния.

## 4. Direct Xray core: когда это было бы лучше

Direct `Xray-core` становится лучше, когда нужны:
- полностью declarative-конфиги и GitOps;
- предсказуемые rollout/rollback без UI;
- жёсткий config-as-code на десятках нод;
- минимизация panel-specific ограничений и дрейфа.

Но это дороже по эксплуатации:
- больше кастомного ops-кода;
- выше требования к операторам;
- больше ответственности на нашей стороне за конфиг-генерацию, валидацию и доставку.

Для текущего single-protocol кластера direct core скорее даст больше ops-работы, чем реальной выгоды.

## 5. Hiddify: стоит ли уходить туда

Короткий ответ: сейчас нет.

Почему:
- Hiddify особенно полезен, когда нужен более широкий протокольный парк и сильнее выраженный panel/client ecosystem;
- у нас текущая продуктовая ставка сейчас не на multi-protocol, а на один стабильный профиль `VLESS/TCP/Reality`;
- миграция control-plane на Hiddify сейчас добавит новый слой сложности, но не даст пропорционального выигрыша именно под текущий scope.

## 6. Рекомендация на сейчас

1. Не мигрировать с `3x-ui` прямо сейчас.
2. Не переписывать всё на direct `Xray-core`, пока нет реальной боли масштаба или GitOps-требования.
3. Держать текущий production-стек:
   - `PORTAL` как source of truth;
   - `3x-ui` как panel/runtime слой;
   - `Xray-core` как data-plane.
4. Усиливать не панель, а эксплуатационную дисциплину:
   - фиксировать runtime facts;
   - пиновать версии `xray-core`;
   - не использовать built-in sub server `3x-ui`;
   - документировать отклонения между panel state и runtime DB.

## 7. Когда стоит вернуться к вопросу миграции

Возвращаться к direct core или Hiddify имеет смысл, если появится хотя бы один из триггеров:
- >10-15 delivery нод;
- частые ручные panel drift-инциденты;
- потребность в строго declarative rollout по нодам;
- потребность в нескольких полноценных протоколах одновременно;
- сильная зависимость операционного качества от panel UI.

## 8. Источники

Primary / official:
- 3x-ui official repository:
  - https://github.com/MHSanaei/3x-ui
- Xray official docs:
  - https://xtls.github.io/en/config/
- Xray-core official repository:
  - https://github.com/XTLS/Xray-core
- Hiddify official GitHub organization:
  - https://github.com/hiddify
- Hiddify official panel repository:
  - https://github.com/hiddify/hiddify-panel

Community / operational context:
- Xray issue about blocking/degradation signals:
  - https://github.com/XTLS/Xray-core/issues/5332
- Habr analysis of current RF blocking context:
  - https://habr.com/ru/articles/969618/

## 9. Bottom line

- `3x-ui` для текущего PORTAL — нормальный выбор, не идеальный, но рациональный.
- Самое важное — не отдавать ей роль source of truth.
- До следующего явного масштабного скачка лучше улучшать docs, monitoring, drift-control и release discipline, а не устраивать миграцию ради миграции.
