"""
WarRoom – SPL Query Templates
=============================
Parameterised Splunk Processing Language (SPL) queries used by the SOC agent
during investigation phases.  Use str.format(**kwargs) to inject values.

All queries target the BOTSv1 dataset by default; swap the index for
production deployments.
"""

from __future__ import annotations

# ── Query catalogue ────────────────────────────────────────────────────
QUERIES: dict[str, str] = {
    # ── Notable / alert triage ─────────────────────────────────────────
    "get_notable_events": (
        "`notable` | head 50 "
        "| table rule_name, severity, src, dest, user, _time"
    ),

    # ── Brute-force detection ──────────────────────────────────────────
    "brute_force_check": (
        'index=botsv1 sourcetype=WinEventLog:Security EventCode=4625 src_ip="{src_ip}" '
        "| stats count by user, src_ip "
        "| where count > 5"
    ),
    "successful_login_after_failures": (
        'index=botsv1 sourcetype=WinEventLog:Security (EventCode=4625 OR EventCode=4624) src_ip="{src_ip}" '
        "| sort _time "
        "| table _time EventCode user src_ip"
    ),

    # ── Lateral movement ───────────────────────────────────────────────
    "lateral_movement": (
        'index=botsv1 src_ip="{src_ip}" '
        "| stats dc(dest_ip) as unique_dests values(dest_ip) as destinations by src_ip "
        "| where unique_dests > 3"
    ),

    # ── Data exfiltration ──────────────────────────────────────────────
    "data_exfiltration": (
        'index=botsv1 src_ip="{src_ip}" '
        "| stats sum(bytes_out) as total_bytes_out by src_ip, dest_ip "
        "| where total_bytes_out > 10000000 "
        "| sort -total_bytes_out"
    ),

    # ── DNS analysis ───────────────────────────────────────────────────
    "dns_activity": (
        'index=botsv1 sourcetype=stream:dns src_ip="{src_ip}" '
        "| stats count avg(query_length) as avg_query_len by query_type "
        "| sort -count"
    ),

    # ── User / entity activity ─────────────────────────────────────────
    "user_activity": (
        'index=botsv1 user="{user}" '
        "| stats count by sourcetype, action "
        "| sort -count"
    ),
    "ip_activity_summary": (
        'index=botsv1 src_ip="{src_ip}" '
        "| stats count by sourcetype "
        "| sort -count"
    ),

    # ── Timeline ───────────────────────────────────────────────────────
    "event_timeline": (
        'index=botsv1 (src_ip="{src_ip}" OR user="{user}") '
        "| sort _time "
        "| table _time sourcetype action src_ip dest_ip user url "
        "| head 50"
    ),

    # ── Web attacks ────────────────────────────────────────────────────
    "web_attacks": (
        'index=botsv1 sourcetype=stream:http src_ip="{src_ip}" '
        '| rex field=uri_path "(?<attack_pattern>(union|select|script|alert|eval|exec))" '
        "| search attack_pattern=* "
        "| table _time src_ip uri_path attack_pattern"
    ),

    # ── Firewall blocks ───────────────────────────────────────────────
    "firewall_blocks": (
        'index=botsv1 sourcetype=firewall action=blocked src_ip="{src_ip}" '
        "| stats count by dest_ip, dest_port "
        "| sort -count"
    ),

    # ── Geolocation ───────────────────────────────────────────────────
    "geo_lookup": (
        'index=botsv1 src_ip="{src_ip}" '
        "| iplocation src_ip "
        "| stats count by Country, City, Region"
    ),
}


def render_query(name: str, **kwargs: str) -> str:
    """
    Render a named SPL query template, substituting the given keyword arguments.

    Raises ``KeyError`` if the query name is unknown or a required placeholder
    is missing from *kwargs*.
    """
    template = QUERIES[name]
    return template.format(**kwargs)
