#!/usr/bin/env python3
"""
Generate static collection pages under docs/collections/.

This keeps the main catalog page dynamic while restoring fork-equivalent
collection-page UX with fully rendered markdown.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import markdown

from catalog_legacy_banner import render_legacy_catalog_banner

REPO_ROOT = Path(__file__).resolve().parent.parent
STYLES_VERSION = "74"


def md_to_html(text: Any) -> str:
    """Render markdown to HTML using the same extensions as the fork."""
    if text is None:
        return ""
    raw = str(text).strip()
    if not raw:
        return ""
    md = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br"])
    return md.convert(raw)


def extract_mcp_configuration_section(deploy_text: str) -> tuple[str, str]:
    """
    Pull ### MCP configuration (and body) out so it is not folded into
    ### Installation (Cursor) / other platform blocks by split_deploy_into_sections.
    """
    pattern = re.compile(
        r"(?:^|\n)(### MCP configuration\s*\n.*?)(?=\n### |\Z)",
        re.DOTALL,
    )
    m = pattern.search(deploy_text)
    if not m:
        return deploy_text, ""
    section = m.group(1).strip()
    rest = deploy_text[: m.start()] + deploy_text[m.end() :]
    return rest.strip(), section


def split_deploy_into_sections(deploy_text: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Split deploy_and_use content into preface + platform install blocks.

    Matches headings like:
      ### Installation (Claude Code)
      ### Installation (Cursor)
      ### Installation (Open Code)

    Call extract_mcp_configuration_section() first so MCP prose is not captured
    inside the last Installation (...) block.
    """
    pattern = re.compile(
        r"### Installation \((Claude Code|Cursor|Open Code)\)\s*\n(.*?)(?=### Installation \(|\Z)",
        re.DOTALL,
    )
    matches = pattern.findall(deploy_text)
    if not matches:
        return deploy_text.strip(), []
    pre_end = deploy_text.find("### Installation (")
    pre_content = deploy_text[:pre_end].strip() if pre_end > 0 else ""
    return pre_content, [(platform, content.strip()) for platform, content in matches]


def format_relative_age(iso_value: str) -> str:
    try:
        dt = datetime.fromisoformat(str(iso_value).replace("Z", "+00:00"))
        delta_seconds = max(
            0, int((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds())
        )
    except ValueError:
        return str(iso_value)
    minutes = delta_seconds // 60
    hours = minutes // 60
    days = hours // 24
    if days > 0:
        return f"{days}d ago"
    if hours > 0:
        return f"{hours}h ago"
    if minutes > 0:
        return f"{minutes}m ago"
    return f"{delta_seconds}s ago"


def _render_eval_skills_banner(es: Dict[str, Any]) -> str:
    """Pack-level eval summary for the Skills tab (HTML-safe)."""
    n = int(es.get("evaluated_count") or 0)
    total = int(es.get("catalog_skill_count") or 0)
    if total <= 0:
        return ""
    coverage_pct = (n / total * 100.0) if total > 0 else 0.0
    latest = html.escape(str(es.get("latest_generated_at") or "N/A"))
    title = f"Evaluation coverage: {n} of {total} skills evaluated ({coverage_pct:.1f}%)"
    if n <= 0:
        note_cls = "muted"
        note = "No evaluations were executed for this pack yet."
    else:
        trials = int(es.get("total_trials_treatment") or 0)
        confidence = str(es.get("confidence_level") or "LOW").upper()
        if confidence == "LOW":
            note_cls = "warn"
            note = f"Low confidence - based on {trials} trial{'s' if trials != 1 else ''}. More evaluations needed for stronger results."
        elif confidence == "MEDIUM":
            note_cls = "warn"
            note = f"Moderate confidence - based on {trials} trial{'s' if trials != 1 else ''}."
        else:
            note_cls = "ok"
            note = f"High confidence - based on {trials} trial{'s' if trials != 1 else ''}."
    return (
        '<div class="collection-eval-summary">'
        '<div class="collection-eval-summary-icon" aria-hidden="true">📊</div>'
        '<div class="collection-eval-summary-body">'
        f'<div class="collection-eval-summary-title">{html.escape(title)}</div>'
        f'<div class="collection-eval-summary-note {note_cls}">{html.escape(note)}</div>'
        '</div>'
        f'<div class="collection-eval-summary-meta"><span>Last evaluated:</span> {latest}</div>'
        "</div>"
    )


def _render_skill_evaluation_block(ev: Dict[str, Any]) -> str:
    """Detailed per-skill evaluation card with trust/evidence focus."""
    rec = str(ev.get("recommendation") or "unknown").strip().lower()
    rec_label = "PASS" if rec == "pass" else ("FAIL" if rec else "UNKNOWN")
    rec_cls = "pass" if rec == "pass" else ("fail" if rec else "unknown")

    def _metric(val: Any, digits: int = 2) -> str:
        return f"{float(val):.{digits}f}" if isinstance(val, (int, float)) else "N/A"

    nt = int(ev.get("n_trials_treatment") or 0)
    nc = int(ev.get("n_trials_control") or 0)
    np_t = int(ev.get("n_passed_treatment") or 0)
    np_c = int(ev.get("n_passed_control") or 0)
    nf_t = int(ev.get("n_failed_treatment") or 0)
    nf_c = int(ev.get("n_failed_control") or 0)
    pr_t = ev.get("pass_rate_treatment")
    if not isinstance(pr_t, (int, float)) and nt > 0:
        pr_t = np_t / nt
    pass_rate_label = (
        f"{int(round(float(pr_t) * 100))}%"
        if isinstance(pr_t, (int, float))
        else ("100%" if rec == "pass" else ("0%" if rec == "fail" else "N/A"))
    )

    conf_label = str(ev.get("confidence_level") or "LOW")
    conf_cls = conf_label.lower()
    has_failures = bool(ev.get("has_failures"))
    failed_trials = int(ev.get("failed_trials") or 0)
    trial_name = html.escape(str(ev.get("latest_trial_name") or "N/A"))
    trial_reward = _metric(ev.get("latest_trial_reward"))
    trial_pass = ev.get("latest_trial_passed")
    trial_status = "PASS" if trial_pass is True else ("FAIL" if trial_pass is False else "N/A")

    mean_t_raw = ev.get("mean_reward_treatment")
    mean_c_raw = ev.get("mean_reward_control")
    mean_t = _metric(mean_t_raw, 2)
    mean_c = _metric(mean_c_raw, 2)
    gap_value = float(ev.get("mean_reward_gap") or 0.0)
    gap_pct_label = f"{gap_value:+.1%}" if gap_value != 0 else "0.0%"
    gap_reward_label = f"{gap_value:+.2f}" if gap_value != 0 else "0.00"

    max_mean = max(
        float(mean_t_raw) if isinstance(mean_t_raw, (int, float)) else 0.0,
        float(mean_c_raw) if isinstance(mean_c_raw, (int, float)) else 0.0,
        0.0001,
    )
    width_t = (
        f"{(float(mean_t_raw) / max_mean) * 100:.1f}%"
        if isinstance(mean_t_raw, (int, float))
        else "0%"
    )
    width_c = (
        f"{(float(mean_c_raw) / max_mean) * 100:.1f}%"
        if isinstance(mean_c_raw, (int, float))
        else "0%"
    )

    coverage_total = int(ev.get("catalog_skill_count") or 0)
    coverage_pct = (nt / coverage_total * 100.0) if coverage_total > 0 else 0.0
    coverage_label = f"{nt} / {coverage_total if coverage_total else 'N/A'}"
    coverage_sub = f"scenarios tested ({coverage_pct:.1f}%)"
    compared_runs = min(nt, nc)
    coverage_signal = (
        f"{nt} of {coverage_total} scenarios tested ({coverage_pct:.1f}%)"
        if coverage_total > 0
        else f"{nt} scenarios tested"
    )

    llm_raw = str(ev.get("llm") or "").strip()
    llm_baseline = re.sub(r"\s*\([^)]*\)\s*$", "", llm_raw).strip() if llm_raw else ""
    llm_baseline_label = html.escape(llm_baseline or "the baseline model")
    llm_baseline_html = f'<span class="model-name">{llm_baseline_label}</span>'
    gap_raw = ev.get("mean_reward_gap")
    if isinstance(gap_raw, (int, float)):
        gap_pct = abs(float(gap_raw) * 100.0)
        if float(gap_raw) > 0:
            plain_summary = (
                f'This skill performed <strong class="skill-eval-delta skill-eval-delta-better">{gap_pct:.1f}% better</strong> '
                f"than vanilla {llm_baseline_html} across {compared_runs} evaluation "
                f'run{"s" if compared_runs != 1 else ""}.'
            )
        elif float(gap_raw) < 0:
            plain_summary = (
                f'This skill performed <strong class="skill-eval-delta skill-eval-delta-worse">{gap_pct:.1f}% worse</strong> '
                f"than vanilla {llm_baseline_html} across {compared_runs} evaluation "
                f'run{"s" if compared_runs != 1 else ""}.'
            )
        else:
            plain_summary = (
                f"This skill performed about the same as vanilla {llm_baseline_html} "
                f'across {compared_runs} evaluation run{"s" if compared_runs != 1 else ""}.'
            )
    else:
        plain_summary = (
            f"Evaluation results are available, but uplift versus vanilla {llm_baseline_html} "
            "is not available yet."
        )

    fisher = ev.get("fisher_p_value")
    significance_text = (
        "Low (insufficient data)"
        if min(nt, nc) < 5
        else (
            "High (statistically significant)"
            if isinstance(fisher, (int, float)) and float(fisher) < 0.05
            else "Moderate (not statistically significant)"
        )
    )
    significance_primary = significance_text.split(" ")[0]

    raw_generated = ev.get("generated_at")
    freshness = (
        format_relative_age(raw_generated)
        if isinstance(raw_generated, str) and raw_generated.strip()
        else "N/A"
    )
    freshness_state = "stale" if "d ago" in freshness and not freshness.startswith("0") else "recent"

    json_url = str(ev.get("report_json_url") or "").strip()
    md_url = str(ev.get("report_md_url") or "").strip()
    report_dir_url = str(ev.get("report_dir_url") or "").strip()
    has_md = bool(ev.get("has_report_md")) and md_url
    generated = html.escape(str(ev.get("generated_at") or "N/A"))
    pipeline = html.escape(str(ev.get("pipeline_run_id") or "N/A"))
    commit_sha = html.escape(str(ev.get("commit_sha") or "N/A"))
    commit_short = commit_sha[:8] if commit_sha != "N/A" else "N/A"
    llm = html.escape(str(ev.get("llm") or "N/A"))
    related_pr = str(ev.get("related_pr") or "").strip()
    pr_match = re.search(r"/pull/(\d+)(?:/|$)", related_pr)
    related_pr_label = f"#{pr_match.group(1)}" if pr_match else ("Open PR" if related_pr else "N/A")
    pass_icon_html = '<span class="skill-pass-icon">✓</span>' if rec_cls == "pass" else ""
    commit_source = str(ev.get("commit_sha") or "").strip()
    commit_short_raw = commit_source[:8] if commit_source else "N/A"
    commit_href = (
        f"https://github.com/RHEcosystemAppEng/skill-submissions/commit/{html.escape(commit_source, quote=True)}"
        if commit_source
        else ""
    )
    commit_html = (
        f'<a class="collection-inline-link" href="{commit_href}" target="_blank" rel="noopener noreferrer">{html.escape(commit_short_raw)} 🔗</a>'
        if commit_href
        else html.escape(commit_short_raw)
    )
    related_pr_html = (
        f'<a class="collection-inline-link" href="{html.escape(related_pr, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(related_pr_label)} 🔗</a>'
        if related_pr
        else "N/A"
    )

    parts = [
        '<div class="skill-eval-card">',
        '<div class="skill-eval-header-grid">',
        '<div class="skill-eval-header-main">',
        f'<div class="skill-eval-plain-summary">{plain_summary}</div>',
        f'<span class="skill-eval-head-badges"><span class="skill-eval-head-badge status {rec_cls}">'
        f'{pass_icon_html}<span>{rec_label}</span></span>'
        f'<span class="skill-eval-head-badge confidence {conf_cls}">{conf_label} confidence</span></span>',
        f'<div class="skill-eval-inline-signals">{coverage_signal}</div>',
        '</div>',
        '<div class="skill-eval-top-meta">',
        '<span class="skill-eval-meta-item">'
        '<svg class="skill-eval-meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M8 2v4"></path><path d="M16 2v4"></path><path d="M3 10h18"></path><path d="M5 6h14a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"></path>'
        '</svg>'
        f'<span>Last evaluated: {html.escape(freshness)} ({freshness_state})</span>'
        '</span>',
        '<span class="skill-eval-meta-item">'
        '<svg class="skill-eval-meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 6h16"></path><path d="M6 12h12"></path><path d="M8 18h8"></path><circle cx="12" cy="12" r="9"></circle>'
        '</svg>'
        f'<span>Model: {llm}</span>'
        '</span>',
        '</div>',
        '</div>',
    ]
    if has_failures:
        parts.append(f'<div class="skill-eval-inline-signals warn">⚠ {failed_trials} failed trial{"s" if failed_trials != 1 else ""}</div>')
    parts.extend(
        [
            '<div class="skill-eval-evidence-row">',
            '<div class="skill-eval-evidence-main">',
            '<div class="evidence-title">✓ Latest verified execution</div>',
            f'<div class="evidence-line">{trial_status} - reward {trial_reward} - {html.escape(freshness)}</div>',
            f'<div class="evidence-line">{trial_name}</div>',
            '</div>',
            '<div class="skill-eval-evidence-links">',
            f'<a class="collection-inline-link" href="{html.escape(md_url or json_url, quote=True)}" target="_blank" rel="noopener noreferrer">View execution details</a>',
            (
                f'<a class="collection-inline-link" href="{html.escape(json_url, quote=True)}" target="_blank" rel="noopener noreferrer">Raw report (JSON)</a>'
                if json_url
                else ""
            ),
            '</div>',
            '</div>',
        ]
    )

    parts.extend(
        [
            '<details class="skill-eval-details">',
            '<summary class="skill-eval-details-summary"><span class="skill-eval-details-title">Technical evaluation details</span><span class="skill-eval-details-subtitle">Coverage, experiments, reproducibility, and raw evaluation artifacts</span><span class="skill-eval-details-chevron" aria-hidden="true"></span>'
            '<span class="skill-eval-details-inline-metrics">'
            f'<span><strong>Coverage</strong> {coverage_label}</span>'
            f'<span><strong>Pass rate</strong> {pass_rate_label}</span>'
            f'<span><strong>Reward</strong> {mean_t}</span>'
            f'<span><strong>Improvement</strong> {gap_pct_label}</span>'
            f'<span><strong>Confidence</strong> {html.escape(significance_primary)}</span>'
            '</span></summary>',
            '<div class="skill-eval-details-body">',
            '<div class="skill-eval-kpis">',
            f'<div class="skill-eval-kpi"><p class="kpi-label">Coverage</p><p class="kpi-value">{coverage_label}</p><p class="kpi-sub">{coverage_sub}</p></div>',
            f'<div class="skill-eval-kpi"><p class="kpi-label">Pass rate (treatment)</p><p class="kpi-value">{pass_rate_label}</p><p class="kpi-sub">{np_t} pass · {nf_t} fail</p></div>',
            f'<div class="skill-eval-kpi"><p class="kpi-label">Reward (treatment)</p><p class="kpi-value">{mean_t}</p><p class="kpi-sub">mean reward</p></div>',
            f'<div class="skill-eval-kpi"><p class="kpi-label">Improvement vs baseline</p><p class="kpi-value">{gap_pct_label}</p><p class="kpi-sub">({gap_reward_label} reward)</p></div>',
            f'<div class="skill-eval-kpi"><p class="kpi-label">Statistical significance</p><p class="kpi-value">{html.escape(significance_text.split(" ")[0])}</p><p class="kpi-sub">{html.escape(significance_text.replace(significance_text.split(" ")[0] + " ", ""))}</p></div>',
            '</div>',
            '<div class="skill-eval-lower-grid">',
            '<div class="skill-eval-compare-card"><p class="group-title">Comparison (mean reward)</p>'
            f'<div class="bar-row"><span>Treatment</span><div class="bar"><i style="width:{width_t}"></i></div><em>{mean_t}</em></div>'
            f'<div class="bar-row"><span>Baseline (control)</span><div class="bar"><i class="control" style="width:{width_c}"></i></div><em>{mean_c}</em></div>'
            '</div>',
            '<div class="skill-eval-group"><p class="group-title">Experiment</p><ul class="group-list">'
            f'<li>Trials: {nt}/{nc} (treatment/control)</li>'
            f'<li>Treatment: {np_t} pass / {nf_t} fail</li>'
            f'<li>Control: {np_c} pass / {nf_c} fail</li>'
            f'<li>Statistical significance: {html.escape(significance_text.lower())}</li>'
            '</ul></div>',
            '<div class="skill-eval-evidence-preview"><div class="evidence-title">✓ Latest verified execution</div>'
            f'<div class="evidence-line">{trial_status} - reward {trial_reward} - {html.escape(freshness)}</div>'
            f'<div class="evidence-line">{trial_name}</div>',
            f'<a class="collection-inline-link" href="{html.escape(md_url or json_url, quote=True)}" target="_blank" rel="noopener noreferrer">View execution details</a>',
            (
                f'<a class="collection-inline-link" href="{html.escape(json_url, quote=True)}" target="_blank" rel="noopener noreferrer">Raw report (JSON)</a>'
                if json_url
                else ""
            ),
            '</div>',
            '</div>',
            '<div class="skill-eval-repro"><strong>Reproducibility</strong>'
            '<div class="skill-eval-repro-labels">'
            '<span>Pipeline</span><span>Commit</span><span>Generated</span><span>Related PR</span>'
            '</div>'
            '<div class="skill-eval-repro-values">'
            f'<span>{pipeline}</span>'
            f'<span>{commit_html}</span>'
            f'<span>{generated}</span>'
            f"<span>{related_pr_html}</span>"
            '</div>'
            '</div>',
            '</div>',
            '</details>',
        ]
    )
    parts.extend(["</div>"])
    return "".join(parts)


def _render_skills_list(skills: List[Dict[str, Any]], pack_name: str, list_tag: str | None = None) -> str:
    items: List[str] = []
    for skill in skills:
        if not isinstance(skill, dict):
            continue
        name = str(skill.get("name", ""))
        desc = html.escape(str(skill.get("description", "")))
        summary = md_to_html(skill.get("summary_markdown", ""))
        skill_path = f"https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/{pack_name}/skills/{name}/SKILL.md"
        heading = f"<div><code>/{html.escape(name)}</code> - {desc}"
        if list_tag:
            heading += f' <span class="skill-kind-badge">{html.escape(list_tag)}</span>'
        heading += "</div>"
        block = [
            "<li>",
            heading,
        ]
        if summary:
            block.append(f"<div class=\"collection-prose collection-prose-tight\">{summary}</div>")
        ev = skill.get("evaluation") if isinstance(skill.get("evaluation"), dict) else None
        if ev:
            block.append(_render_skill_evaluation_block(ev))
        block.append(
            f"<a class=\"collection-inline-link\" href=\"{skill_path}\" target=\"_blank\" rel=\"noopener noreferrer\">"
            "View SKILL.md on GitHub -></a>"
        )
        block.append("</li>")
        items.append("\n".join(block))
    return f"<ol class=\"collection-skill-list\">{''.join(items)}</ol>" if items else ""


def _render_decision_guide(rows: List[Dict[str, Any]]) -> str:
    body_rows: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        user_request = md_to_html(row.get("user_request", row.get("user_quote", "")))
        skill_to_use = str(row.get("skill_to_use", ""))
        if skill_to_use and not skill_to_use.startswith("/"):
            skill_to_use = f"/{skill_to_use}"
        reason = md_to_html(row.get("reason", ""))
        body_rows.append(
            "<tr>"
            f"<td>{user_request}</td>"
            f"<td>{html.escape(skill_to_use)}</td>"
            f"<td>{reason}</td>"
            "</tr>"
        )
    if not body_rows:
        return ""
    return (
        "<table class=\"collection-decision-table\">"
        "<thead><tr><th>User request</th><th>Skill to use</th><th>Reason</th></tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )


def _render_resources(resources: List[Dict[str, Any]], pack_name: str) -> str:
    if not resources:
        return "<p class=\"collection-missing\">No resources.</p>"

    out = ["<h2>References</h2>", "<ul class=\"simple-list collection-resources\">"]
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        title = html.escape(str(resource.get("title", "")))
        description = html.escape(str(resource.get("description", "")))
        url = str(resource.get("url", "")).strip()
        embedded = str(resource.get("embedded_doc", "")).strip()
        line = ["<li>"]
        if url:
            safe_url = html.escape(url, quote=True)
            line.append(
                f'<a class="collection-resource-link" href="{safe_url}" '
                'target="_blank" rel="noopener noreferrer">'
                f"{title}</a>"
            )
        else:
            line.append(f"<strong>{title}</strong>")
        if description:
            line.append(f" - {description}")
        if embedded:
            embed_url = (
                "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/"
                f"{pack_name}/{embedded.lstrip('/')}"
            )
            line.append(
                f' <a class="collection-inline-link" href="{html.escape(embed_url, quote=True)}" '
                'target="_blank" rel="noopener noreferrer">[embedded doc]</a>'
            )
        line.append("</li>")
        out.append("".join(line))
    out.append("</ul>")
    return "".join(out)


def _render_agents_tab(
    workflows: List[Dict[str, Any]],
    mcp_servers: List[Dict[str, Any]],
) -> str:
    out: List[str] = ["<h2>MCP Server Integrations</h2>"]
    if mcp_servers:
        out.append('<div class="collection-mcp-grid">')
        for server in mcp_servers:
            title = html.escape(str(server.get("title") or server.get("name") or ""))
            owner = html.escape(str(server.get("owner") or "Red Hat"))
            server_type = "HTTP Remote" if server.get("type") == "http" else "Container"
            icon = str(server.get("icon") or "")
            icon_html = f"<span>{html.escape(icon)}</span>" if icon else ""
            pack = html.escape(str(server.get("pack") or ""))
            name = html.escape(str(server.get("name") or ""))
            out.append(
                '<div class="collection-mcp-card" role="button" tabindex="0" '
                f'data-mcp-pack="{pack}" data-mcp-name="{name}">'
                f'<div class="collection-mcp-card-title">{icon_html}<span>{title}</span></div>'
                f'<div class="collection-mcp-card-meta">By {owner} - {server_type}</div>'
                "</div>"
            )
        out.append("</div>")
    else:
        out.append(
            "<p class=\"collection-missing\">No MCP servers are associated with this pack in the published site data.</p>"
        )

    out.append("<h2>Sample Workflows</h2>")
    valid_workflows = [
        w for w in workflows if isinstance(w, dict) and w.get("name") != "TODO: Add workflow"
    ]
    if not valid_workflows:
        valid_workflows = [{"name": "See collection.yaml", "workflow": "Add workflows in collection.yaml."}]
    for wf in valid_workflows:
        name = html.escape(str(wf.get("name", "")))
        workflow_html = md_to_html(wf.get("workflow", ""))
        out.append(f"<h3>{name}</h3>")
        out.append(f"<div class=\"collection-prose\">{workflow_html}</div>")
    return "".join(out)


def render_collection_page(pack: Dict[str, Any], mcp_data: List[Dict[str, Any]]) -> str:
    """Render a full static collection page for one pack."""
    collection = pack.get("collection") or {}
    collection_id = (
        collection.get("id")
        or pack.get("plugin", {}).get("name")
        or pack.get("name")
    )
    page_title = collection.get("name") or pack.get("plugin", {}).get("title") or pack.get("name")
    description = str(collection.get("description") or "").strip()
    subtitle = html.escape(description[:120].strip() + ("..." if len(description) > 120 else ""))
    yaml_link = (
        "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/"
        f"{pack['name']}/.catalog/collection.yaml"
    )
    readme_link = (
        "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/"
        f"{pack['name']}/README.md"
    )
    categories = collection.get("categories") or []
    personas = collection.get("personas") or []
    version = pack.get("plugin", {}).get("version")
    meta_line_parts: List[str] = [f"<strong>Module:</strong> {html.escape(str(pack['name']))}"]
    if version:
        meta_line_parts.append(html.escape(f"v{version}"))
    if personas:
        meta_line_parts.append(html.escape(", ".join(str(p) for p in personas)))
    metadata_line_html = f'<p class="collection-page-sub">{" · ".join(meta_line_parts)}</p>'

    # Overview tab
    overview_parts: List[str] = []
    if collection.get("summary"):
        overview_parts.append("<h2>Overview</h2>")
        overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(collection.get('summary'))}</div>")
    if collection.get("documentation_section"):
        overview_parts.append("<h2>Documentation</h2>")
        overview_parts.append(
            f"<div class=\"collection-prose\">{md_to_html(collection.get('documentation_section'))}</div>"
        )
    if collection.get("mcp_section"):
        overview_parts.append("<h2>MCP</h2>")
        overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(collection.get('mcp_section'))}</div>")
    if collection.get("deploy_and_use"):
        overview_parts.append("<h2>Quick Start</h2>")
        deploy_raw = str(collection.get("deploy_and_use"))
        deploy_for_installs, mcp_deploy_section = extract_mcp_configuration_section(deploy_raw)
        pre_content, install_sections = split_deploy_into_sections(deploy_for_installs)
        if pre_content:
            overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(pre_content)}</div>")
        if install_sections:
            overview_parts.append('<div class="install-accordion">')
            for idx, (platform, content) in enumerate(install_sections):
                open_attr = " open" if idx == 0 else ""
                overview_parts.append(
                    f'<details class="install-accordion-item"{open_attr}>'
                    f'<summary class="install-accordion-header">Installation ({html.escape(platform)})</summary>'
                    f'<div class="install-accordion-body collection-prose">{md_to_html(content)}</div>'
                    "</details>"
                )
            overview_parts.append("</div>")
        if mcp_deploy_section:
            overview_parts.append(
                f'<div class="collection-prose collection-mcp-after-install">{md_to_html(mcp_deploy_section)}</div>'
            )
    if collection.get("security_model"):
        overview_parts.append("<h2>Security Model</h2>")
        overview_parts.append(f"<div class=\"collection-prose\">{md_to_html(collection.get('security_model'))}</div>")

    # Skills tab
    contents = collection.get("contents") or {}
    skills_parts = ["<h2>Skills</h2>"]
    esum = pack.get("evaluation_summary") or {}
    if int(esum.get("catalog_skill_count") or 0) > 0:
        skills_parts.append(_render_eval_skills_banner(esum))
    if contents.get("description"):
        skills_parts.append(f"<div class=\"collection-prose\">{md_to_html(contents.get('description'))}</div>")
    orchestration = contents.get("orchestration_skills") or []
    skills = contents.get("skills") or []
    if orchestration:
        skills_parts.append(f"<h3>{'Orchestration Skill' if len(orchestration) == 1 else 'Orchestration Skills'}</h3>")
        skills_parts.append(_render_skills_list(orchestration, pack["name"], "Orchestration skill"))
    if skills:
        skills_parts.append(f"<h3>{'Basic Skills' if orchestration else 'Skills'}</h3>")
        skills_parts.append(_render_skills_list(skills, pack["name"]))
    guide = contents.get("skills_decision_guide") or []
    if guide:
        skills_parts.append("<h2>Skills Decision Guide</h2>")
        skills_parts.append(_render_decision_guide(guide))
    if not orchestration and not skills and not guide and not contents.get("description"):
        skills_parts.append("<p class=\"collection-missing\">No skills content.</p>")

    # Resources tab
    resources_html = _render_resources(collection.get("resources") or [], pack["name"])

    # Agents tab
    pack_mcp = [s for s in mcp_data if s.get("pack") == pack.get("name")]
    agents_html = _render_agents_tab(collection.get("sample_workflows") or [], pack_mcp)

    category_line = (
        f'<p class="collection-tags"><strong>Categories:</strong> {html.escape(", ".join(str(c) for c in categories))}</p>'
        if categories
        else ""
    )
    repo_footer = (
        f'<p class="collection-footer-meta">{html.escape(str(collection.get("repository")))}</p>'
        if collection.get("repository")
        else ""
    )

    legal = collection.get("legal_resources") or {}
    license_nav_href = str(legal.get("license_agreement_url") or "").strip()
    if not license_nav_href:
        license_nav_href = "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main/LICENSE"
    license_nav_href_esc = html.escape(license_nav_href, quote=True)

    legacy_banner = render_legacy_catalog_banner()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(str(page_title))} - Red Hat Agentic Catalog</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Red+Hat+Text:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css?v={STYLES_VERSION}">
</head>
<body>
    {legacy_banner}
    <div class="site-brand-accent" aria-hidden="true"></div>
    <main>
        <section class="collection-page">
            <div class="collection-page-inner collection-content">
                <nav class="collection-nav" aria-label="Collection">
                    <div class="collection-nav-start">
                        <a href="../index.html" class="collection-back">← Back to Catalog</a>
                    </div>
                    <div class="collection-nav-center">
                        <a href="{html.escape(yaml_link, quote=True)}" target="_blank" rel="noopener noreferrer" class="collection-meta-link">catalog YAML →</a>
                    </div>
                    <div class="collection-nav-end">
                        <a href="{html.escape(readme_link, quote=True)}" target="_blank" rel="noopener noreferrer" class="collection-meta-link">README →</a>
                        <a href="{license_nav_href_esc}" target="_blank" rel="noopener noreferrer" class="collection-meta-link">Apache 2.0 License →</a>
                    </div>
                </nav>
                <div class="collection-page-body collection-content-inner">
                    <h1 class="collection-page-title">{html.escape(str(page_title))}</h1>
                    <p class="collection-page-sub">{subtitle}</p>
                    {metadata_line_html}
                    {category_line}

                    <div class="collection-tabs" role="tablist">
                        <button type="button" class="collection-tab active" data-tab="overview" role="tab" aria-selected="true" aria-controls="tab-overview">Overview</button>
                        <button type="button" class="collection-tab" data-tab="skills" role="tab" aria-selected="false" aria-controls="tab-skills">Skills</button>
                        <button type="button" class="collection-tab" data-tab="resources" role="tab" aria-selected="false" aria-controls="tab-resources">Resources</button>
                        <button type="button" class="collection-tab" data-tab="agents" role="tab" aria-selected="false" aria-controls="tab-agents">Agents</button>
                    </div>

                    <div id="tab-overview" class="collection-tab-panel active" role="tabpanel">{''.join(overview_parts)}</div>
                    <div id="tab-skills" class="collection-tab-panel" role="tabpanel">{''.join(skills_parts)}</div>
                    <div id="tab-resources" class="collection-tab-panel" role="tabpanel">{resources_html}</div>
                    <div id="tab-agents" class="collection-tab-panel" role="tabpanel">{agents_html}</div>

                    {repo_footer}
                </div>
            </div>
        </section>
    </main>

    <div id="mcp-modal" class="modal">
        <div class="modal-content" id="mcp-details"></div>
    </div>

    <script src="../app.js?v={STYLES_VERSION}"></script>
</body>
</html>
"""


def generate_collection_pages(pack_data: List[Dict[str, Any]], mcp_data: List[Dict[str, Any]]) -> int:
    """Generate docs/collections/*.html and return generated page count."""
    out_dir = REPO_ROOT / "docs" / "collections"
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_files = set()
    count = 0
    for pack in pack_data:
        if not pack.get("collection"):
            continue
        collection = pack.get("collection") or {}
        collection_id = (
            collection.get("id")
            or pack.get("plugin", {}).get("name")
            or pack.get("name")
        )
        file_name = f"{collection_id}.html"
        generated_files.add(file_name)
        page_html = render_collection_page(pack, mcp_data)
        (out_dir / file_name).write_text(page_html, encoding="utf-8")
        count += 1

    # Remove stale collection pages
    for page in out_dir.glob("*.html"):
        if page.name not in generated_files:
            page.unlink()

    return count

