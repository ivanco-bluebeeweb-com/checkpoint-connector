# Pricing History — Check Point Connector

Обязательный журнал: каждое выставление или изменение цен на функции этого
приложения фиксируется здесь — что изменилось, почему, и на основании чего.
Не переписывать прошлые записи — только дописывать новые сверху.

---

## 2026-08-24 — прайсинг ЗАБЛОКИРОВАН системным багом платформы (task #2260)

Приложение задеплоено и полностью работает (26/27 проверок валидатора,
30 инструментов синхронизировано), но прайсинг выставить НЕ УДАЛОСЬ.

Каждый вызов `developer.update_pricing` (несколько разных payload —
полный набор `tool_prices`, минимальный `{"currency": "tokens"}`,
однокелючевой `{"tool_prices": {"list_hosts": 8}}`), `developer.save_pricing`,
и `developer.bulk_set_pricing` возвращал идентичную ошибку:

```
1 validation error for UpdatePricingParams
pricing_config
  Input should be a valid dictionary [type=dict_type, input_value='{...}', input_type=str]
```

т.е. объектный/массивный параметр (`pricing_config`, `tool_prices`,
`app_ids`) приходил как JSON-строка вместо реального dict/list ДО
pydantic-валидации — независимо от содержимого. Это не тот же класс
ошибки, что "первая попытка молча не сохраняет, повтор проходит",
задокументированный у Zscaler/Cisco Secure Access/Fortinet/Palo Alto
Networks Connector — здесь жёсткая validation error на КАЖДОЙ попытке,
без единого успешного вызова.

Эта ошибка уже задокументирована как известный системный баг в
**Imperal Cloud, task #2260** (впервые обнаружен на `mirth-connect-connector`).
Добавлен комментарий с новым воспроизведением на `checkpoint-connector`
(2026-08-24) с полным списком опробованных вариантов вызова.

**Запланированные цены (та же fixed-scale модель {0, 8, 16, 40, 60}, что
Zscaler/Cisco Secure Access/Fortinet/Palo Alto Networks Connector) —
применить, как только баг #2260 будет устранён:**
- `0` — connect_checkpoint/list_connections/disconnect_checkpoint
- `8` — все list_*/get_*-функции (hosts/networks/groups/services/access
  layers/rules/policy packages/task status/gateways)
- `16` — все write-операции (create/update/delete/publish/discard/
  install_policy)
- `40` — audit_checkpoint_estate
- `60` — bulk_access_rule_action

Приложение отправлено на ревью БЕЗ прайсинга (`submit_for_review`),
т.к. функционал сам по себе полностью работает, а блокер — платформенный,
не связан с кодом приложения.
