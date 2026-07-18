"""Legroom Learn — offline session learning for coding agents.

Analyzes conversation logs using an LLM to extract actionable patterns
and generates context (CLAUDE.md, AGENTS.md, GEMINI.md, etc.) that
prevents future token waste.

Plugin architecture:
    plugins/claude.py  ─┐
    plugins/codex.py   ─┤→  Analyzer (LLM)  →  Writer (adapter)
    plugins/gemini.py  ─┤
    plugins/grok.py    ─┘

Built-in plugins are auto-discovered from legroom.learn.plugins.*.
External plugins register via the ``legroom.learn_plugin`` entry point.
"""
