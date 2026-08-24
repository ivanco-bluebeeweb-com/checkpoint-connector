# Check Point Connector — Preparation (Фаза 2.5, до кода)

**Дата:** 2026-08-24. Основано на `CONNECTOR_DISCOVERY.md`. SASE/SIEM-серия —
"максимальный функционал, полный максимум" заявлен заранее для всей
категории, повторный вопрос не требуется.

## 1. WHY BYOK

Check Point Security Management Server живёт в собственной сети клиента
(on-prem или private cloud appliance) — тот же принцип, что
Fortinet/Palo Alto Networks/Cisco Secure Access Connector: Imperal не
брокерит доступ централизованно.

## 2. WHY ОДИН connect_*, а не несколько (в отличие от Fortinet/PAN-OS)

Fortinet различает FortiGate/FortiManager/FortiSASE, PAN-OS — firewall/
Panorama, потому что это архитектурно разные продукты с разными API. У
Check Point ОДИН тип управляющего сервера — Security Management Server
(или Multi-Domain Server как надстройка над тем же API с доп. параметром
`domain`) — и gateways сами по себе не выставляют независимого API для
этого коннектора: они управляются исключительно через Management API.
Поэтому здесь один `connect_checkpoint`, с опциональным полем `domain`
для MDS-инсталляций, а не два независимых пути.

## 3. WHY session-token (`sid` + `X-chkp-sid`), а не Bearer/API key

Check Point Management API — explicitly session-based (см.
CONNECTOR_DISCOVERY.md §1): `login` возвращает `sid` с скользящим
таймаутом (~600s активности). Коннектор обязан прозрачно повторно
логиниться при истечении сессии (401 или `generic_err_*` о невалидном
sid) — тот же lazy-refresh принцип, что OAuth2 client_credentials у
других коннекторов портфеля, но триггер — HTTP 401 или конкретный код
ошибки в теле, а не истёкший JWT.

## 4. WHY publish/discard как отдельный обязательный write-инструмент

Ключевое архитектурное отличие Check Point от всех остальных SASE-коннекторов
портфеля: write-операции (add-host, set-access-rule, ...) видны ТОЛЬКО
внутри текущей сессии, пока не вызван `publish`. Это НЕ то же самое, что
FortiGate/PAN-OS commit (тот применяет к device немедленно после явного
commit) — здесь ещё один промежуточный слой: session-local staging area,
которая должна быть либо `publish`, либо `discard`. Коннектор обязан дать
оба инструмента как явные write-функции, а не автоматически publish-ить
после каждого изменения (пользователь может захотеть накопить несколько
изменений перед одним publish, штатный Check Point workflow).

## 5. WHY install-policy отдельно от publish

`publish` сохраняет изменения в policy database, но НЕ разворачивает их на
gateways — для этого отдельный `install-policy` (асинхронная задача,
polled через `show-task`). Явное разделение "сохранить" vs "развернуть на
устройства" — тот же принцип, что Panorama commit (сохранить локально) vs
push (развернуть на managed devices), но здесь это единая цепочка:
publish -> install-policy -> show-task, три отдельных вызова.

## 6. WHY access layers как обязательный параметр rulebase-операций

Check Point поддерживает несколько ordered policy layers на один package
(в отличие от плоского rulebase Fortinet/PAN-OS) — rulebase-операции
(list/create/update/delete rules) обязаны принимать `layer` как параметр,
без разумного дефолта (нет единого "Layer1" на всех инсталляциях) —
`list_access_layers` идёт первым шагом дискавери, аналогично тому, как
Panorama требует явный `device_group`.

## 7. Итоговый набор функций (максимальный функционал)

- **Connection:** connect_checkpoint, disconnect_checkpoint, list_connections.
- **Objects:** hosts (CRUD), networks (CRUD), groups (list/create), services
  TCP/UDP (CRUD).
- **Access Control:** list_access_layers, list_access_rules, get_access_rule,
  create_access_rule, update_access_rule, delete_access_rule.
- **Policy lifecycle:** publish_changes, discard_changes, list_policy_packages,
  install_policy, get_task_status.
- **Inventory:** list_gateways.
- **Bulk + audit (Tier 3):** bulk_access_rule_action, audit_checkpoint_estate.

## 8. Naming discipline

Единый префикс, без per-surface разделения (в отличие от Fortinet's
fortigate_/fortimanager_/fortisase_) — всё это один API поверх одного
Management Server, поэтому имена инструментов плоские: `list_hosts`,
`create_access_rule`, `publish_changes` и т.д., без суффикса поверхности.
