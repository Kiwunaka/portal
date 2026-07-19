import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


RULE_CASES = {
    "android_battery_background": {
        "positive": (
            "Android закрывает POKROV в фоне.",
            "На Android POKROV останавливается при выключении экрана.",
            "POKROV выгружается из фона на Android.",
        ),
        "negated": "Android не закрывает POKROV в фоне, проблема только со скоростью.",
        "adjacent": "Android просит разрешить VPN-подключение.",
        "mixed": "Android закрывает POKROV в фоне, а Hiddify пустой после импорта.",
        "out_of_scope": "Проверь мой аккаунт Android в базе данных.",
    },
    "connected_no_internet": {
        "positive": (
            "POKROV подключён, но интернета нет.",
            "Соединение установлено, а сайты не открываются.",
            "Подключение активно, но трафик не проходит.",
        ),
        "negated": "POKROV подключён, интернет работает нормально.",
        "adjacent": "v2rayNG подключается, но интернета нет.",
        "mixed": "POKROV подключён без интернета, и соединение очень медленное.",
        "out_of_scope": "Проверь мой аккаунт и почему там нет интернета.",
    },
    "device_limit_help": {
        "positive": (
            "Не могу добавить устройство из-за лимита.",
            "Достигнут лимит устройств.",
            "Приложение пишет, что устройств слишком много.",
        ),
        "negated": "Лимит устройств не достигнут.",
        "adjacent": "Какие ограничения у Premium?",
        "mixed": "Достигнут лимит устройств, и соединение стало медленным.",
        "out_of_scope": "Проверь мой аккаунт и удали старое устройство.",
    },
    "happ_import": {
        "positive": (
            "Как импортировать профиль в Happ?",
            "Как добавить подписку POKROV в Happ?",
            "Нужно вставить профиль в Happ.",
        ),
        "negated": "Профиль уже импортирован в Happ и работает.",
        "adjacent": "Happ подключается, но интернета нет.",
        "mixed": "Как импортировать профиль одновременно в Happ и v2rayNG?",
        "out_of_scope": "Откройте мой аккаунт и импортируйте профиль в Happ.",
    },
    "hiddify_empty_profile": {
        "positive": (
            "В Hiddify профиль пустой после импорта.",
            "Hiddify показывает пустой список серверов.",
            "После добавления подписки в Hiddify ничего нет.",
        ),
        "negated": "Профиль Hiddify не пустой и серверы видны.",
        "adjacent": "Как импортировать профиль в Hiddify?",
        "mixed": "Hiddify пустой после импорта, и соединение очень медленное.",
        "out_of_scope": "Проверьте мой профиль Hiddify на сервере.",
    },
    "hiddify_import": {
        "positive": (
            "Как импортировать профиль в Hiddify?",
            "Как добавить подписку POKROV в Hiddify?",
            "Нужно вставить профиль в Hiddify.",
        ),
        "negated": "Профиль уже импортирован в Hiddify.",
        "adjacent": "В Hiddify пустой список серверов.",
        "mixed": "Как импортировать профиль в Hiddify и Happ одновременно?",
        "out_of_scope": "Выполни команду импорта профиля Hiddify на сервере.",
    },
    "karing_import": {
        "positive": (
            "Как импортировать профиль в Karing?",
            "Как добавить подписку POKROV в Karing?",
            "Нужно вставить профиль в Karing.",
        ),
        "negated": "Профиль уже импортирован в Karing.",
        "adjacent": "Karing подключён без интернета.",
        "mixed": "Как импортировать профиль в Karing и Streisand?",
        "out_of_scope": "Откройте мой аккаунт и настройте Karing.",
    },
    "one_site_not_open": {
        "positive": (
            "Один сайт не открывается, остальные работают.",
            "Не работает только конкретный сайт.",
            "Все сайты кроме одного открываются.",
        ),
        "negated": "Нет такого, что не открывается только один сайт.",
        "adjacent": "Все сайты не открываются после подключения.",
        "mixed": "Один сайт не открывается, и скорость очень низкая.",
        "out_of_scope": "Проверь на сервере, почему заблокирован мой сайт.",
    },
    "other_network_client_conflict": {
        "positive": (
            "Может ли другой VPN мешать POKROV?",
            "На устройстве включены два VPN одновременно.",
            "Ещё один VPN-клиент конфликтует с POKROV.",
        ),
        "negated": "Другой VPN не включён и конфликта нет.",
        "adjacent": "Как выбрать клиент для Android?",
        "mixed": "Другой VPN мешает POKROV, и один сайт не открывается.",
        "out_of_scope": "Выполни команду удаления другого VPN с устройства.",
    },
    "private_dns_and_filters": {
        "positive": (
            "Может ли Private DNS мешать POKROV?",
            "Как проверить частный DNS?",
            "Фильтр DNS ломает подключение.",
        ),
        "negated": "Private DNS отключён и не мешает.",
        "adjacent": "POKROV подключён, но интернета нет.",
        "mixed": "Private DNS мешает, и профиль Hiddify пустой.",
        "out_of_scope": "Выполни команду изменения Private DNS на устройстве.",
    },
    "refresh_after_renewal": {
        "positive": (
            "После продления приложение показывает старый срок.",
            "Продлил доступ, но срок не обновился.",
            "После продления нужно обновить доступ.",
        ),
        "negated": "После продления новый срок уже появился.",
        "adjacent": "Оплата не применилась к аккаунту.",
        "mixed": "После продления старый срок, и Hiddify пустой.",
        "out_of_scope": "Проверь мою оплату и обнови срок в базе.",
    },
    "routing_all_except_ru": {
        "positive": (
            "Российские сайты напрямую, остальные через POKROV.",
            "Сайты РФ хочу открывать без VPN, другие через POKROV.",
            "Нужен режим: RU напрямую, остальное через POKROV.",
        ),
        "negated": "Не хочу открывать российские сайты напрямую.",
        "adjacent": "Весь трафик нужно пустить через POKROV.",
        "mixed": "Российские сайты напрямую, но один иностранный сайт не открывается.",
        "out_of_scope": "Проверь мой аккаунт и поменяй режим маршрутизации.",
    },
    "slow_speed": {
        "positive": (
            "Через POKROV очень низкая скорость.",
            "После подключения всё работает медленно.",
            "Соединение POKROV тормозит.",
        ),
        "negated": "Скорость не низкая, всё работает быстро.",
        "adjacent": "Один сайт не открывается, остальные быстрые.",
        "mixed": "Скорость низкая, и профиль Hiddify пустой.",
        "out_of_scope": "Проверь скорость моего сервера из базы.",
    },
    "streisand_import": {
        "positive": (
            "Как импортировать профиль в Streisand?",
            "Как добавить подписку POKROV в Streisand?",
            "Нужно вставить профиль в Streisand.",
        ),
        "negated": "Профиль уже импортирован в Streisand.",
        "adjacent": "Какой клиент выбрать для iPhone?",
        "mixed": "Как импортировать профиль в Streisand и Karing?",
        "out_of_scope": "Выполни команду настройки Streisand на устройстве.",
    },
    "v2rayn_import": {
        "positive": (
            "Как импортировать профиль в v2rayN?",
            "Как добавить подписку POKROV в v2rayN?",
            "Нужно вставить профиль в v2rayN на Windows.",
        ),
        "negated": "Профиль уже импортирован в v2rayN.",
        "adjacent": "В v2rayN режим TUN оставляет программы без сети.",
        "mixed": "Как импортировать профиль в v2rayN и v2rayNG?",
        "out_of_scope": "Выполни команду настройки v2rayN на компьютере.",
    },
    "v2rayn_proxy_tun": {
        "positive": (
            "В v2rayN часть программ без сети из-за TUN.",
            "После включения TUN в v2rayN программы не работают.",
            "На Windows v2rayN конфликтует с системным прокси.",
        ),
        "negated": "TUN в v2rayN не включён и программы работают.",
        "adjacent": "Как импортировать профиль в v2rayN?",
        "mixed": "TUN в v2rayN ломает сеть, и скорость низкая.",
        "out_of_scope": "Запусти команду и исправь TUN на моём Windows.",
    },
    "v2rayng_import": {
        "positive": (
            "Как импортировать профиль в v2rayNG?",
            "Как добавить подписку POKROV в v2rayNG?",
            "Нужно вставить профиль в v2rayNG на Android.",
        ),
        "negated": "Профиль уже импортирован в v2rayNG.",
        "adjacent": "v2rayNG подключается, но интернета нет.",
        "mixed": "Как импортировать профиль в v2rayNG и Happ?",
        "out_of_scope": "Выполни команду настройки v2rayNG на телефоне.",
    },
    "v2rayng_no_internet": {
        "positive": (
            "v2rayNG подключается, но интернета нет.",
            "В v2rayNG соединение активно, а сайты не открываются.",
            "v2rayNG показывает подключение без трафика.",
        ),
        "negated": "v2rayNG подключён и интернет работает.",
        "adjacent": "Как импортировать профиль в v2rayNG?",
        "mixed": "v2rayNG без интернета, и достигнут лимит устройств.",
        "out_of_scope": "Проверь мой профиль v2rayNG на сервере.",
    },
}


@pytest.fixture
def repo_grounding_engine():
    from support_agent_grounding import SupportGroundingEngine
    from support_agent_knowledge import SupportKnowledgeStore

    store = SupportKnowledgeStore()
    knowledge = store.load(REPO_ROOT / "shared" / "support-ai-knowledge.json")
    return SupportGroundingEngine(store, knowledge)


@pytest.fixture
def grounding_engine(repo_grounding_engine):
    return repo_grounding_engine


@pytest.fixture
def policy_snapshot():
    from support_agent_policy import SupportAgentPolicyStore

    return SupportAgentPolicyStore().load(
        REPO_ROOT / "shared" / "support-agent-policy.json"
    )


def test_each_rule_has_three_positive_and_four_negative_classes(grounding_engine):
    from support_agent_safety import InputDisposition, classify_support_input

    for topic_id, cases in RULE_CASES.items():
        assert len(cases["positive"]) == 3
        for prompt in cases["positive"]:
            decision = grounding_engine.select(prompt, None)
            assert decision.disposition.value == "confident"
            assert decision.grounding_topic_id == topic_id
        assert grounding_engine.select(cases["negated"], None).grounding_topic_id != topic_id
        assert grounding_engine.select(cases["adjacent"], None).grounding_topic_id != topic_id
        assert grounding_engine.select(cases["mixed"], None).disposition.value != "confident"
        assert (
            classify_support_input(cases["out_of_scope"]).disposition
            is InputDisposition.LOCAL_ESCALATE
        )


def test_confident_and_candidate_coverage_is_non_vacuous(repo_grounding_engine):
    bundle = json.loads(
        (REPO_ROOT / "tests/fixtures/support-agent-live-eval.json").read_text(
            encoding="utf-8"
        )
    )
    confident = 0
    correct = 0
    top_three = 0
    for case in bundle["normal"]:
        decision = repo_grounding_engine.select(case["prompt"], None)
        accepted = set(case["accepted_topic_ids"])
        confident += int(decision.disposition.value == "confident")
        correct += int(decision.grounding_topic_id in accepted)
        top_three += int(bool(accepted & set(decision.context_topic_ids)))
    assert confident >= 12
    assert correct == confident
    assert top_three >= 46


def test_all_ten_session_openers_are_confident(repo_grounding_engine):
    bundle = json.loads(
        (REPO_ROOT / "tests/fixtures/support-agent-live-eval.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(bundle["sessions"]) == 10
    for case in bundle["sessions"]:
        decision = repo_grounding_engine.select(case["turns"][0], None)
        assert decision.grounding_topic_id == case["expected_issue_topic_id"]


def test_body_hash_mismatch_downgrades_and_disables_local_render(
    repo_grounding_engine,
    policy_snapshot,
):
    from support_agent_grounding import LOCAL_RENDERABLE_TOPICS, SupportGroundingEngine

    decision = repo_grounding_engine.select(
        "POKROV подключён, но интернета нет.", None
    )
    broken_bindings = dict(LOCAL_RENDERABLE_TOPICS)
    broken_bindings["connected_no_internet"] = "0" * 64
    broken_engine = SupportGroundingEngine(
        repo_grounding_engine.knowledge_store,
        repo_grounding_engine.knowledge,
        local_renderable_topics=broken_bindings,
    )
    downgraded = broken_engine.select(
        "POKROV подключён, но интернета нет.", None
    )
    assert decision.disposition.value == "confident"
    assert downgraded.disposition.value == "candidate"
    assert broken_engine.render_local(downgraded, policy_snapshot) is None


def test_renderer_version_mismatch_downgrades_and_disables_local_render(
    repo_grounding_engine,
    policy_snapshot,
):
    from support_agent_grounding import SupportGroundingEngine

    broken_engine = SupportGroundingEngine(
        repo_grounding_engine.knowledge_store,
        repo_grounding_engine.knowledge,
        local_renderer_version="local-body-v0",
    )
    downgraded = broken_engine.select(
        "POKROV подключён, но интернета нет.", None
    )
    assert downgraded.disposition.value == "candidate"
    assert downgraded.grounding_topic_id is None
    assert broken_engine.render_local(downgraded, policy_snapshot) is None


def test_local_renderer_uses_only_bound_body_and_fixed_safe_frame(
    repo_grounding_engine,
    policy_snapshot,
):
    decision = repo_grounding_engine.select(
        "POKROV подключён, но интернета нет.", None
    )
    reply = repo_grounding_engine.render_local(decision, policy_snapshot)

    assert reply is not None
    assert reply.startswith("Коротко\n")
    assert "\n\nЕсли не поможет\nНапишите в поддержку." in reply
    assert "http://" not in reply and "https://" not in reply
    assert len(reply) <= 1_200


def test_retriever_hash_changes_with_rule_content():
    from support_agent_grounding import (
        INTENT_RULES,
        RETRIEVER_RULES_SHA256,
        _retriever_rules_sha256,
    )

    changed = (
        replace(
            INTENT_RULES[0],
            forbidden_phrases=(*INTENT_RULES[0].forbidden_phrases, "new phrase"),
        ),
        *INTENT_RULES[1:],
    )
    assert len(RETRIEVER_RULES_SHA256) == 64
    assert _retriever_rules_sha256(INTENT_RULES) == RETRIEVER_RULES_SHA256
    assert _retriever_rules_sha256(changed) != RETRIEVER_RULES_SHA256


def test_retrieval_limit_is_closed_and_applied(repo_grounding_engine):
    from support_agent_grounding import SupportGroundingEngine

    with pytest.raises(ValueError, match="grounding_retrieval_limit_invalid"):
        SupportGroundingEngine(
            repo_grounding_engine.knowledge_store,
            repo_grounding_engine.knowledge,
            retrieval_limit=4,
        )
    bounded = SupportGroundingEngine(
        repo_grounding_engine.knowledge_store,
        repo_grounding_engine.knowledge,
        retrieval_limit=1,
    )
    assert len(bounded.select("Подключено, но сайты не открываются", None).context_topics) == 1
