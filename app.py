"""The simple student-facing screen (Gradio). Start the API first, then:  python app.py
Gradio turns Python functions into a web page, so no HTML or JavaScript is needed."""
import os

import gradio as gr
import requests

API = os.getenv("API_URL", "http://localhost:8000")
TYPES = ["scholarship", "internship", "job", "learning"]
LEVELS = ["100", "200", "300", "400", "500", "postgraduate", "graduate"]


def find(course, level, interests, looking_for, show_examples):
    body = {
        "profile": {
            "course": course, "level": level or "",
            "interests": [i.strip() for i in interests.split(",") if i.strip()],
            "looking_for": looking_for,
        },
        "explain": True, "include_examples": show_examples,
    }
    try:
        r = requests.post(f"{API}/match", json=body, timeout=300)
        r.raise_for_status()
    except requests.RequestException as e:
        return f"Could not reach the API at {API}. Is it running?\n\n{e}"
    results = r.json()
    if not results:
        return "No open opportunities match yet. Try fewer filters."
    out = []
    for m in results:
        o = m["opportunity"]
        out.append(f"### {o['name']}  \n*{o['type']} · {o['organisation']}*")
        out += [f"- {x}" for x in m["reasons"]]
        if m["explanation"]:
            out.append(f"\n{m['explanation']}")
        out.append(f"\n[Verify on the official page]({o['link']})\n")
    return "\n".join(out)


def draft(raw_text, source_link, new_id):
    try:
        r = requests.post(f"{API}/extract", json={"raw_text": raw_text,
                          "source_link": source_link, "new_id": new_id}, timeout=300)
    except requests.RequestException as e:
        return {"error": str(e)}
    return r.json()


with gr.Blocks(title="OppFinder") as demo:
    gr.Markdown("# OppFinder\nFind scholarships, internships, jobs and learning opportunities you may qualify for. "
                "Always confirm details on the official page.")
    with gr.Tab("Find opportunities"):
        course = gr.Textbox(label="Your course", placeholder="Computer Science")
        level = gr.Dropdown(LEVELS, label="Level")
        interests = gr.Textbox(label="Interests (comma separated)", placeholder="data, AI, writing")
        looking_for = gr.CheckboxGroup(TYPES, label="Looking for (leave empty for all)")
        show_examples = gr.Checkbox(label="Show placeholder examples (for testing)", value=False)
        go = gr.Button("Find")
        result = gr.Markdown()
        go.click(find, [course, level, interests, looking_for, show_examples], result)
    with gr.Tab("Add an opportunity (team use)"):
        raw = gr.Textbox(label="Paste the announcement text", lines=8)
        link = gr.Textbox(label="Official link")
        nid = gr.Textbox(label="New id (e.g. scholarship-chevening-2026)")
        btn = gr.Button("Draft record with the model")
        out = gr.JSON(label="Draft: check it carefully, then save with POST /opportunities")
        btn.click(draft, [raw, link, nid], out)

if __name__ == "__main__":
    demo.launch()
