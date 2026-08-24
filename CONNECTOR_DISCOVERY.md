# Check Point Connector — API discovery (Фаза 2, до кода)

Источник: Check Point Management API (`web_api`) — R80.x/R81.x Security
Management Server / Multi-Domain Server, REST-подобный JSON API поверх
HTTPS. Официальная площадка `sc1.checkpoint.com/documents/latest/APIs/`
(CLI `mgmt_cli` — тот же API другим транспортом).

## 1. Форма аутентификации — session-based, НЕ statless Bearer

- `POST /web_api/login` с `{"user": ..., "password": ..., "domain": ...?}`
  возвращает `sid` (session id) + `session-timeout` (обычно 600s, но
  сессия активно используется, таймаут скользящий).
- Каждый последующий запрос обязан нести заголовок `X-chkp-sid: <sid>`
  (НЕ `Authorization: Bearer`).
- `POST /web_api/logout` явно закрывает сессию.
- При `domain` (Multi-Domain Security Management, MDS) — логин либо в
  конкретный Domain Management Server, либо в Global; без MDS параметр
  просто опускается.

## 2. WHY session + publish/discard — ключевое отличие от Fortinet/PAN-OS

Все write-операции (`add-host`, `set-access-rule`, `delete-network`, ...)
изменяют ТОЛЬКО текущую сессию — они невидимы другим сессиям и не
применяются к political database, пока не вызван `POST /web_api/publish`.
`POST /web_api/discard` откатывает все несохранённые изменения сессии.
Это отдельная, третья фаза поверх аналогичного FortiGate
config-then-commit и PAN-OS config-then-commit паттерна: здесь unit
транзакции — вся сессия, а не единичный commit XML. Коннектор обязан
дать явный `publish_changes` инструмент, аналогично `commit_config`
Fortinet/PAN-OS.

## 3. Установка политики — install-policy, отдельная от publish

`POST /web_api/install-policy` с `{"policy-package": ..., "targets": [...]}`
разворачивает УЖЕ опубликованную политику на конкретные gateways/clusters.
Асинхронная задача — возвращает `task-id`, статус читается через
`show-task`. Аналог push_to_devices у Panorama, но с обязательным
предварительным publish.

## 4. Объекты политики (аналог address/service objects Fortinet/PAN-OS)

- Hosts: `show-hosts`/`show-host`, `add-host`, `set-host`, `delete-host`
  (поле `ipv4-address`).
- Networks: `show-networks`/`show-network`, `add-network`, `set-network`,
  `delete-network` (`subnet4` + `subnet-mask` или `mask-length4`).
- Groups: `show-groups`, `add-group` (`members: [...]`).
- Services (TCP/UDP): `show-services-tcp`, `add-service-tcp` (`port`),
  аналогично `-udp`.

## 5. Access Control Policy (аналог security rules)

- Access layers: `show-access-layers` (топ-уровневые policy layers —
  Check Point поддерживает несколько ordered layers на один package).
  Rulebase операции обязательно скопированы к конкретному `layer`.
- `show-access-rulebase` (`{"name": <layer>}`) — список правил с позицией.
- `add-access-rule` (`layer`, `position`, `source`, `destination`,
  `service`, `action` = Accept/Drop/Reject, `track` — логирование).
- `set-access-rule`/`delete-access-rule` по `uid` или `name`+`layer`.

## 6. Gateways & clusters (read-only inventory)

`show-gateways-and-servers` — список managed gateways/clusters с их
именами/IP/версией ПО/статусом политики (used as install-policy targets
list AND as the estate-health surface, аналог Fortinet managed devices).

## 7. Policy packages

`show-packages`/`show-package` — именованные policy packages (пара из
Access + NAT + Threat Prevention layers), нужны как `policy-package`
параметр install-policy.

## 8. Session/task lifecycle helpers

`show-session` (детали текущей сессии, включая изменения, ожидающие
publish), `show-task` (статус асинхронной задачи, напр. install-policy).

## 9. Ошибки и коды

Check Point возвращает HTTP 200 почти всегда, ошибки — в теле JSON под
`code`/`message` (напр. `generic_err_invalid_parameter`,
`generic_err_object_not_found`) либо HTTP 401 при истёкшей/невалидной
сессии — клиент обязан явно опознать 401 и вернуть понятную ошибку
"session expired, reconnect", а не тихо падать.

## 10. Итоговая архитектура коннектора

Один connect_* (`connect_checkpoint`) — Management Server — плюс weekly
session-token client (аналог FortiManager, но с publish/discard/task
поверх, а не JSON-RPC). НЕ разделяем на несколько connect_* — в отличие
от Fortinet/PAN-OS, здесь только ОДИН тип сервера (Security Management
Server), gateways сами по себе не имеют независимого API для этого
коннектора — они управляются через management API.
