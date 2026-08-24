# Check Point Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на функционале `checkpoint-connector` (см.
`PREPARATION.md`).

**ВАЖНО (усвоено на Zscaler/Cisco Secure Access/Fortinet/Palo Alto
Networks Connector — реальные ошибки DUI-валидатора, не повторять):**
`ui.Stack` НЕ принимает `width=`. `ui.Stats` принимает
`children=[ui.Stat(...)]`, НЕ `stats=[...]`/`items=[dict]`. `ui.Alert`
принимает `type=`, НЕ `variant=`. `ui.Badge` принимает `label=`/`color=`,
НЕ `text=`/`variant=`. `ui.ListItem` принимает `title=`/`subtitle=`, НЕ
`label=`. `ui.Input`/`ui.Password`/`ui.Select` НЕ принимают `label=` —
использовать соседний `ui.Text(..., variant="caption")` внутри
`ui.Stack(direction="v", gap=1)`. Модалка помощи регистрируется как
`@ext.panel(..., slot="center", center_overlay=True)` и открывается через
`ui.Call("__panel__<name>")`, НЕ через несуществующий `@ext.modal`.
`main.py` ОБЯЗАН импортировать `panels_center`, иначе overlay-панели не
регистрируются несмотря на корректный код.

## 0. Разница с реализацией сейчас

Реализация начинается с нуля вместе с этим документом — план строится
ПЕРЕД `panels.py`, по правилу APP_PREPARATION_STANDARD.md §9. Начальный
`panels.py` реализует ровно §1 ниже.

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Stack`(direction="v") + `ui.Text`(connection summary) + `ui.Divider` + navigation `ui.ListItem`(Access Control / Objects / Gateways / Health) + `ui.Button`("App settings") | Без карточек, как весь остальной SASE-набор. |
| Connect form | `ui.Stack`(direction="v", gap=1, children=[`ui.Text`("Management Server host", variant="caption"), `ui.Input`(param_name="host", placeholder="https://mgmt.company.com")]) + аналогично username/domain + Password для password + submit `ui.Button` | Каждый инпут с явным лейблом-соседом, контекстный placeholder; форма растянута на всю ширину сайдбара, её содержимое растянуто внутри неё. |
| Empty (no connection) | `ui.Empty`(message="Connect your Check Point Management Server first.", icon="Shield") | Стандартный пустой экран первого запуска. |
| Help modal | `@ext.panel("checkpoint_connect_help", slot="center", center_overlay=True)` с пошаговым текстом (роль администратора, что делает login-обмен, что такое domain) | Единственное место с инструкцией — не дублируется в сайдбаре. |
| Access Control overview (center overlay) | `ui.Stack` + `ui.Text`(layer name) + список правил через `ui.ListItem`(title=rule name, subtitle=action, badge=`ui.Badge`(disabled/enabled)) | Плоский список, без карточек. |
| Objects overview (center overlay) | Аналогичные `ui.ListItem` списки для hosts/networks/groups/services | Единый паттерн отображения списков во всём портфеле. |
| Gateways overview (center overlay) | `ui.Stack` + `ui.ListItem`(title=gateway name, subtitle=IP, badge=policy status) | Инвентарь managed gateways. |
| App settings (center overlay) | `ui.Stack` + список подключений с `ui.Button`("Disconnect", variant="danger") на каждом | Единственное место с disconnect, не дублируется в сайдбаре формы. |

## 2. Что строится СЕЙЧАС (во время создания приложения, не после)

`panels.py` (сайдбар + connect form + help modal wiring) создаётся сразу
после `app.py`/`schemas.py`/клиента/`handlers_connection.py` — до
написания остальных handlers-модулей, ровно как этот документ требует:
интерфейс строится ВО ВРЕМЯ создания приложения, в правильном месте
этапа, не после.
