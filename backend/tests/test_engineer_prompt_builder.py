from app.agents.prompts.engineer import build_engineer_system_prompt


def test_engineer_prompt_includes_react_block_for_react_framework() -> None:
    prompt = build_engineer_system_prompt(language="javascript", framework="react")

    assert "ABSOLUTE RULES - NEVER VIOLATE THESE:" in prompt
    assert "LANGUAGE-SPECIFIC RULES (JAVASCRIPT):" in prompt
    assert "FRAMEWORK-SPECIFIC RULES (REACT) - CRITICAL:" in prompt
    assert "OUTPUT RULES:" in prompt


def test_engineer_prompt_uses_generic_block_for_unknown_language_and_framework() -> None:
    prompt = build_engineer_system_prompt(language="unknown", framework="unknown")

    assert "GENERIC RULES:" in prompt
    assert "FRAMEWORK-SPECIFIC RULES (REACT) - CRITICAL:" not in prompt


def test_engineer_prompt_handles_case_insensitive_keys() -> None:
    prompt = build_engineer_system_prompt(language="PyThOn", framework="FlAsK")

    assert "LANGUAGE-SPECIFIC RULES (PYTHON):" in prompt
    assert "FRAMEWORK-SPECIFIC RULES (FLASK):" in prompt
