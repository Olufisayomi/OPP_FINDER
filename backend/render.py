"""Turns the /match response into readable Markdown for the screen.
Kept separate from app.py so it can be tested without Gradio."""


def to_markdown(data: dict) -> str:
    matches = data.get("matches", [])
    near = data.get("near_misses", [])
    if not matches and not near:
        return ("No open opportunities match yet. Try fewer filters, or check the spelling of your course.")
    out = []
    if matches:
        out.append("## You can apply for these\n")
        for m in matches:
            o = m["opportunity"]
            out.append(f"### {o['name']}  \n*{o['type']} · {o['organisation']}*")
            out += [f"- {x}" for x in m["reasons"]]
            if m.get("explanation"):
                out.append(f"\n{m['explanation']}")
            out.append(f"\n[Verify on the official page]({o['link']})\n")
    else:
        out.append("## You can apply for these\n\nNothing matches your details right now.\n")
    if near:
        out.append("## Not eligible yet: what is missing and what to do\n")
        for n in near:
            o = n["opportunity"]
            out.append(f"### {o['name']}  \n*{o['type']} · {o['organisation']}*")
            out += [f"- {g}" for g in n["gaps"]]
            out.append(f"\n{n.get('explanation') or n.get('next_step', '')}")
            out.append(f"\n[Verify on the official page]({o['link']})\n")
    return "\n".join(out)
