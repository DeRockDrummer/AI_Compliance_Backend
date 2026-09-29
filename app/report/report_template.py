def render_report(compliance_json: dict) -> str:
    """
    Convert compliance JSON into a formatted text block.
    Later we will replace this with a real Jinja2 template.
    """

    lines = []
    lines.append("AI Compliance Report")
    lines.append("====================")
    lines.append("")
    lines.append(f"Overall Score: {compliance_json['overall_score']}")
    lines.append(f"Framework: {compliance_json['framework']}")
    lines.append("")

    lines.append("Controls:")
    for c in compliance_json["controls"]:
        lines.append(f"- {c['id']} ({c['name']}): {c['status']} — {c['details']}")

    lines.append("")
    lines.append("Risks:")
    if compliance_json["risks"]:
        for r in compliance_json["risks"]:
            lines.append(f"- {r['id']} ({r['severity']}): {r['description']}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Recommendations:")
    if compliance_json["recommendations"]:
        for rec in compliance_json["recommendations"]:
            lines.append(f"- {rec}")
    else:
        lines.append("- None")

    return "\n".join(lines)


