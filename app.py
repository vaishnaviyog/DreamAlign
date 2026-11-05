import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Careers: the traits each one needs, plus a short description.
# ---------------------------------------------------------------------------
CAREERS = {
    "Software Engineer": (["Coding", "Problem Solving", "Analytical Thinking", "Independent Work"],
                          "Design, develop, and maintain software systems."),
    "AI/ML Engineer": (["Coding", "Problem Solving", "Analytical Thinking", "Math Skills", "Data Analysis"],
                       "Build AI and machine learning models for intelligent systems."),
    "Data Scientist": (["Data Analysis", "Math Skills", "Analytical Thinking", "Independent Work"],
                       "Analyze data, uncover insights, and build predictive models."),
    "Mechanical Engineer": (["Problem Solving", "Team Work", "Practical Thinking", "Hands-On Work"],
                            "Design and build mechanical systems and machinery."),
    "Civil Engineer": (["Team Work", "Practical Thinking", "Leadership", "Field Work"],
                       "Plan, design, and oversee construction projects."),
    "Electrical Engineer": (["Analytical Thinking", "Problem Solving", "Hands-On Work", "Coding"],
                            "Design electrical systems and circuits."),
    "Biotechnologist": (["Lab Work", "Analytical Thinking", "Detail-Oriented", "Research Skills"],
                        "Work on biological systems and innovations in life sciences."),
    "Physicist": (["Analytical Thinking", "Problem Solving", "Research Skills", "Math Skills"],
                  "Study the fundamental laws of nature and physical phenomena."),
    "Chemist": (["Lab Work", "Math Skills", "Detail-Oriented", "Research Skills"],
                "Perform experiments and research in chemistry laboratories."),
    "Environmental Scientist": (["Research Skills", "Team Work", "Analytical Thinking", "Field Work"],
                                "Research environmental issues and find sustainable solutions."),
    "Chartered Accountant": (["Analytical Thinking", "Detail-Oriented", "Independent Work", "Finance Knowledge"],
                             "Manage financial records and advise businesses on finances."),
    "Financial Analyst": (["Data Analysis", "Finance Knowledge", "Analytical Thinking", "Team Work"],
                          "Analyze financial data and guide investment decisions."),
    "Investment Banker": (["Analytical Thinking", "Finance Knowledge", "Leadership", "Risk Taking"],
                          "Advise on financial transactions and investments."),
    "Economist": (["Research Skills", "Analytical Thinking", "Data Analysis", "Finance Knowledge"],
                  "Analyze economic trends and provide insights for policy and business."),
    "Marketing Specialist": (["Creativity", "Team Work", "Communication", "Problem Solving"],
                             "Plan and execute marketing strategies for products and services."),
    "Entrepreneur": (["Leadership", "Risk Taking", "Problem Solving", "Creativity"],
                     "Start and manage businesses, taking calculated risks."),
    "UX Designer": (["Creativity", "Problem Solving", "Team Work", "Design Skills"],
                    "Design user-friendly digital interfaces and experiences."),
    "Digital Marketing Specialist": (["Creativity", "Communication", "Data Analysis", "Risk Taking"],
                                     "Promote brands online using creative, data-driven strategies."),
    "Content Creator": (["Creativity", "Communication", "Independent Work", "Risk Taking"],
                        "Create engaging digital content across platforms."),
    "Product Manager": (["Leadership", "Team Work", "Problem Solving", "Communication"],
                        "Oversee product development and strategy."),
    "Cybersecurity Expert": (["Problem Solving", "Coding", "Analytical Thinking", "Detail-Oriented"],
                             "Protect digital systems from cyber threats."),
    "Renewable Energy Engineer": (["Team Work", "Field Work", "Hands-On Work", "Problem Solving"],
                                  "Design and implement renewable energy solutions."),
    "Bioinformatics Specialist": (["Coding", "Lab Work", "Data Analysis", "Research Skills"],
                                  "Analyze biological data using computational methods."),
    "Blockchain Developer": (["Coding", "Analytical Thinking", "Risk Taking", "Independent Work"],
                             "Develop decentralized applications and blockchain systems."),
    "Astrophysicist": (["Analytical Thinking", "Research Skills", "Math Skills", "Independent Work"],
                       "Research celestial phenomena and theoretical physics."),
}

# ---------------------------------------------------------------------------
# Questions: each option awards points to one or more traits.
# ---------------------------------------------------------------------------
SCALE = [("Yes, love it", 2), ("Sometimes", 1), ("Not really", 0)]


def scale(*traits):
    """Build Yes / Sometimes / No options that score the given traits."""
    return [(label, {t: pts for t in traits}) for label, pts in SCALE]


QUESTIONS = [
    ("Which activity do you enjoy most?", "🎯", [
        ("Coding / programming", {"Coding": 2}),
        ("Lab experiments", {"Lab Work": 2, "Research Skills": 1}),
        ("Analyzing money & markets", {"Finance Knowledge": 2, "Data Analysis": 1}),
        ("Creative work / design", {"Creativity": 2, "Design Skills": 2}),
        ("Building or fixing things", {"Hands-On Work": 2, "Practical Thinking": 1}),
    ]),
    ("How do you prefer to work?", "🤝", [
        ("Independently", {"Independent Work": 2}),
        ("In a team", {"Team Work": 2}),
        ("Leading a group", {"Leadership": 2, "Team Work": 1}),
    ]),
    ("Which skill is your strength?", "💪", [
        ("Problem solving", {"Problem Solving": 2}),
        ("Analytical thinking", {"Analytical Thinking": 2}),
        ("Creativity", {"Creativity": 2}),
        ("Communication", {"Communication": 2}),
        ("Attention to detail", {"Detail-Oriented": 2}),
    ]),
    ("Which environment do you prefer?", "🏢", [
        ("Laboratory / research", {"Lab Work": 2, "Research Skills": 1}),
        ("Fieldwork / outdoors", {"Field Work": 2}),
        ("Office / desk job", {"Detail-Oriented": 1, "Independent Work": 1}),
        ("Flexible / startup", {"Risk Taking": 1, "Creativity": 1}),
        ("Workshop / on-site", {"Hands-On Work": 1, "Practical Thinking": 1}),
    ]),
    ("Are you comfortable with numbers & data?", "📊", scale("Data Analysis", "Math Skills")),
    ("Do you enjoy coding or programming?", "💻", scale("Coding")),
    ("Do you enjoy conducting experiments?", "🧪", scale("Lab Work", "Research Skills")),
    ("Do you enjoy leading projects or teams?", "🧭", scale("Leadership")),
    ("Do you enjoy hands-on practical work?", "🔧", scale("Hands-On Work", "Practical Thinking")),
    ("Are you comfortable taking risks?", "🎲", scale("Risk Taking")),
    ("Do you enjoy explaining ideas, writing or presenting?", "🎤", scale("Communication")),
    ("Do you enjoy solving real-world problems?", "🌍", scale("Problem Solving", "Practical Thinking")),
]

# Highest score each trait can reach across the whole quiz (used to normalise).
MAX_TRAIT = {}
for _, _, _options in QUESTIONS:
    for trait in {t for _, pts in _options for t in pts}:
        MAX_TRAIT[trait] = MAX_TRAIT.get(trait, 0) + max(pts.get(trait, 0) for _, pts in _options)

# Fail fast if a career needs a trait the quiz can never measure.
_missing = {t for traits, _ in CAREERS.values() for t in traits} - MAX_TRAIT.keys()
assert not _missing, f"Traits not covered by any question: {_missing}"


def score_answers(answers):
    """Return (ranked careers as [(name, percent)], trait strengths as {trait: 0..1})."""
    totals = {}
    for (_, _, options), choice in zip(QUESTIONS, answers):
        for trait, pts in options[choice][1].items():
            totals[trait] = totals.get(trait, 0) + pts
    strength = {t: min(totals.get(t, 0) / MAX_TRAIT[t], 1.0) for t in MAX_TRAIT}

    ranked = []
    for name, (traits, _) in CAREERS.items():
        pct = round(100 * sum(strength[t] for t in traits) / len(traits))
        ranked.append((name, pct))
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked, strength


@app.route("/")
def home():
    return render_template("index.html", n_questions=len(QUESTIONS), n_careers=len(CAREERS))


@app.route("/quiz")
def quiz():
    return render_template("quiz.html", questions=QUESTIONS)


@app.route("/results", methods=["GET", "POST"])
def results():
    if request.method == "GET":
        return redirect(url_for("quiz"))

    answers = []
    for i, (_, _, options) in enumerate(QUESTIONS, start=1):
        raw = request.form.get(f"q{i}", "")
        if not raw.isdigit() or int(raw) >= len(options):
            return redirect(url_for("quiz"))
        answers.append(int(raw))

    ranked, strength = score_answers(answers)
    top3 = ranked[:3]
    top_strengths = [t for t, s in sorted(strength.items(), key=lambda kv: -kv[1]) if s > 0][:5]
    matches = {
        name: [t for t in CAREERS[name][0] if strength[t] >= 0.5]
        for name, _ in top3
    }
    return render_template(
        "results.html",
        top3=top3,
        chart=ranked[:8],
        careers=CAREERS,
        matches=matches,
        top_strengths=top_strengths,
    )


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
