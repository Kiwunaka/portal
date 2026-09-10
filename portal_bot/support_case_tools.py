"""Case-only tools. Model arguments never choose an account, path or provider URL."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from support_case_context import load_case, read_case, pending_case_message, safe_text


def _tool(name, description, properties=None):
    properties = properties or {}
    return {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties,
                           "required": list(properties), "additionalProperties": False}}


CASE_TOOLS = [
    _tool("read_account", "Текущий доступ и виды подтверждённых входов этого аккаунта."),
    _tool("read_payments", "Последние заказы этого аккаунта и свежая GET-проверка доступных счетов провайдера."),
    _tool("read_access_history", "События выдачи доступа, обработки оплаты и действий оператора."),
    _tool("read_diagnostics", "Исторические сводки диагностики этого обращения."),
    _tool("read_attachments", "Прочитать последние два вложения обращения: текст, изображения, PDF через Vision."),
    _tool("read_node_status", "Последние серверные измерения узлов, связанных с этим аккаунтом. Это снимок, не живой тест."),
    _tool("search_knowledge", "Найти проверенную инструкцию POKROV по вопросу.",
          {"query": {"type": "string", "minLength": 1, "maxLength": 300}}),
    _tool("write_case_note", "Подготовить внутреннюю заметку: факты, что неизвестно и что проверить оператору. Сохранение вместе с итоговым ответом.",
          {"text": {"type": "string", "minLength": 1, "maxLength": 1800}}),
    _tool("request_operator", "Подготовить передачу обращения в очередь оператора. Выполнится вместе с итоговым ответом.",
          {"reason": {"type": "string", "minLength": 1, "maxLength": 500},
           "queue": {"type": "string", "enum": ["billing", "connection", "account", "general"]}}),
    _tool("propose_action", "Подготовить для оператора конкретное действие и основания. Не исполняет действие и не создаёт платёжный intent.",
          {"action": {"type": "string", "enum": ["review_payment", "review_access", "review_refund", "review_connection"]},
           "reason": {"type": "string", "minLength": 1, "maxLength": 800}}),
]


class CaseTools:
    def __init__(self, owner_id, ticket_id, bot=None):
        self.owner_id, self.ticket_id, self.bot = owner_id, ticket_id, bot
        self.revision = None
        self.actions = []
        self.trace = []
        self.facts = {}
        self.history = []
        self.has_attachments = False

    async def start(self):
        from db import SessionLocal
        def read():
            with SessionLocal() as session:
                revision = pending_case_message(session, self.owner_id, self.ticket_id)
                if revision is not None:
                    data, files, _ = read_case(session, self.owner_id, self.ticket_id)
                    self.history = data["messages"]
                    self.has_attachments = bool(files)
                return revision
        self.revision = await asyncio.to_thread(read)
        return self.revision is not None

    async def execute(self, name, args, *, analyze_attachment, search):
        schema = next((t["parameters"] for t in CASE_TOOLS if t["name"] == name), None)
        if schema is None or not isinstance(args, dict) or set(args) != set(schema["properties"]):
            return {"error": "invalid_arguments"}
        for key, rule in schema["properties"].items():
            value = args[key]
            if (not isinstance(value, str) or not value.strip() or len(value) > rule.get("maxLength", 100)
                    or ("enum" in rule and value not in rule["enum"])):
                return {"error": "invalid_arguments"}
        from db import SessionLocal
        def check():
            with SessionLocal() as session:
                return pending_case_message(session, self.owner_id, self.ticket_id) == self.revision
        if self.revision is None or not await asyncio.to_thread(check):
            return {"error": "case_changed"}
        self.trace.append(name)
        if name == "search_knowledge":
            return {"source": "approved_knowledge", "topics": search(safe_text(args["query"], 300))}
        if name in {"write_case_note", "request_operator", "propose_action"}:
            # At most one of each operation per turn; later edits replace the draft.
            self.actions = [a for a in self.actions if a["name"] != name]
            self.actions.append({"name": name, **{k: safe_text(v, 1800) for k, v in args.items()}})
            return {"status": "staged", "commits_with_reply": True}
        if name == "read_node_status":
            return await asyncio.to_thread(self._nodes)
        section, keys = {
            "read_account": ("account", ("access", "identities")),
            "read_payments": ("payments", ("payments",)),
            "read_access_history": ("history", ("payment_events", "operator_events", "account_events")),
            "read_diagnostics": ("diagnostics", ("diagnostics",)),
            "read_attachments": ("attachments", ("attachments",)),
        }[name]
        data = await load_case(self.owner_id, self.ticket_id, self.bot,
                               analyze_attachment=analyze_attachment, section=section)
        if data.get("operator_handling"):
            return {"error": "case_changed"}
        result = {k: data[k] for k in ("source", "as_of_utc", *keys)}
        self.facts.update(result)
        return result

    def _nodes(self):
        from db import SessionLocal
        from models import User, AccessKey, NodeRuntimeMetric
        with SessionLocal() as session:
            user = session.get(User, self.owner_id)
            owners = ([r.tg_id for r in session.query(User.tg_id).filter_by(account_id=user.account_id)]
                      if user.account_id else [self.owner_id])
            codes = [r.node_code for r in session.query(AccessKey.node_code).filter(
                AccessKey.tg_id.in_(owners), AccessKey.state == "active").distinct().limit(8)]
            result = []
            for code in codes:
                metric = session.query(NodeRuntimeMetric).filter_by(node_code=code).order_by(
                    NodeRuntimeMetric.sampled_at.desc(), NodeRuntimeMetric.id.desc()).first()
                if metric:
                    result.append({"sampled_at": metric.sampled_at.isoformat(),
                                   "dataplane_ok": metric.dataplane_ok,
                                   "edge_reachability_ok": metric.edge_reachability_ok,
                                   "authenticated_egress_ok": metric.authenticated_egress_ok})
            return {"source": "stored_node_metrics_not_live_probe", "nodes": result}


def persist_case_actions(session, ticket_id: int, actions: tuple) -> bool:
    """Caller holds the ticket/revision lock; commit atomically with public reply."""
    from models import SupportTicket
    from tickets_repo import add_ticket_message
    ticket = session.get(SupportTicket, ticket_id)
    escalated = False
    for action in actions:
        name = action["name"]
        if name == "write_case_note":
            body = "AI-разбор: " + action["text"]
        elif name == "propose_action":
            body = "AI-предложение для проверки оператором (не исполнено): " + action["action"] + ". " + action["reason"]
        elif name == "request_operator":
            ticket.queue = action["queue"]
            ticket.waiting_on = "operator"
            ticket.escalated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            body = "AI передал на проверку оператору: " + action["reason"]
            escalated = True
        else:
            raise ValueError("unsupported_case_action")
        add_ticket_message(session, ticket_id=ticket_id, sender_tg_id=0,
                           sender_role="assistant", visibility="internal", body=body,
                           macro_code="ai_case_" + name)
    return escalated
