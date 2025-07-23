import markdown
from jinja2 import Template


def get_notes(slide):
    if "\n^" not in slide:
        return ""

    notes_idx = slide.index("\n^")
    notes = slide[notes_idx:].replace("^ ", "")
    return markdown.markdown(notes)


if __name__ == "__main__":
    with open("template.html") as f:
        template = Template(f.read())

    with open("input.md") as f:
        file_contents = f.read()

    slides = map(get_notes, file_contents.split("\n---\n"))

    with open("output.html", "w") as f:
        f.write(template.render(slides=slides))
