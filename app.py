import io
import json
import os
from flask import Flask, abort, redirect, render_template, request, send_file, url_for

app = Flask(__name__)

# Données en mémoire (remises à zéro au redémarrage)
EXERCICES = []
SEANCES = []
PROGRAMMES = []

_next_ids = {"exercice": 1, "seance": 1, "programme": 1}


def next_id(kind):
    nid = _next_ids[kind]
    _next_ids[kind] += 1
    return nid


def find_by_id(items, item_id):
    for item in items:
        if item["id"] == item_id:
            return item
    return None


# ── Index ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("programmes"))


# ── Programmes ───────────────────────────────────────────────────────────────

@app.route("/programmes")
def programmes():
    return render_template("programmes.html", programmes=PROGRAMMES, active_tab="programmes")


@app.route("/programmes/creer", methods=["GET", "POST"])
def programme_creer():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        seance_ids = [int(i) for i in request.form.getlist("seances")]
        if nom:
            PROGRAMMES.append({"id": next_id("programme"), "nom": nom, "seances": seance_ids})
        return redirect(url_for("programmes"))
    return render_template("programme_form.html", seances=SEANCES, active_tab="programmes")


@app.route("/programmes/<int:programme_id>")
def programme_detail(programme_id):
    programme = find_by_id(PROGRAMMES, programme_id)
    if not programme:
        abort(404)
    seances = [find_by_id(SEANCES, sid) for sid in programme["seances"]]
    return render_template(
        "programme_detail.html",
        programme=programme,
        seances=seances,
        active_tab="programmes",
    )


# ── Séances ──────────────────────────────────────────────────────────────────

@app.route("/seances")
def seances():
    return render_template("seances.html", seances=SEANCES, active_tab="seances")


@app.route("/seances/creer", methods=["GET", "POST"])
def seance_creer():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        blocs = _parse_seance_blocs(request)
        if nom:
            SEANCES.append({"id": next_id("seance"), "nom": nom, "blocs": blocs})
        return redirect(url_for("seances"))
    return render_template("seance_form.html", seance=None, exercices=sorted(EXERCICES, key=lambda e: e["nom"].lower()), active_tab="seances")


def _parse_seance_blocs(request):
    """Parse the items_json field from a séance form."""
    raw = request.form.get("items_json", "[]")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []


@app.route("/seances/<int:seance_id>")
def seance_detail(seance_id):
    seance = find_by_id(SEANCES, seance_id)
    if not seance:
        abort(404)
    exercices_map = {e["id"]: e for e in EXERCICES}
    return render_template(
        "seance_detail.html",
        seance=seance,
        exercices_map=exercices_map,
        active_tab="seances",
    )


@app.route("/seances/<int:seance_id>/modifier", methods=["GET", "POST"])
def seance_modifier(seance_id):
    seance = find_by_id(SEANCES, seance_id)
    if not seance:
        abort(404)
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        blocs = _parse_seance_blocs(request)
        if nom:
            seance["nom"] = nom
            seance["blocs"] = blocs
        return redirect(url_for("seance_detail", seance_id=seance_id))
    return render_template("seance_form.html", seance=seance, exercices=sorted(EXERCICES, key=lambda e: e["nom"].lower()), active_tab="seances")


@app.route("/seances/<int:seance_id>/supprimer", methods=["POST"])
def seance_supprimer(seance_id):
    global SEANCES
    SEANCES = [s for s in SEANCES if s["id"] != seance_id]
    for prog in PROGRAMMES:
        prog["seances"] = [sid for sid in prog["seances"] if sid != seance_id]
    return redirect(url_for("seances"))


# ── Exercices ─────────────────────────────────────────────────────────────────

@app.route("/exercices")
def exercices():
    sorted_exercices = sorted(EXERCICES, key=lambda e: e["nom"].lower())
    return render_template("exercices.html", exercices=sorted_exercices, active_tab="exercices")


@app.route("/exercices/creer", methods=["GET", "POST"])
def exercice_creer():
    if request.method == "POST":
        exercice = _parse_exercice_form(request)
        if exercice:
            EXERCICES.append(exercice)
        return redirect(url_for("exercices"))
    return render_template("exercice_form.html", exercice=None, active_tab="exercices")


@app.route("/exercices/<int:exercice_id>")
def exercice_detail(exercice_id):
    exercice = find_by_id(EXERCICES, exercice_id)
    if not exercice:
        abort(404)
    return render_template("exercice_detail.html", exercice=exercice, active_tab="exercices")


def _parse_exercice_form(request, existing_id=None):
    """Parse exercise form: nom + description + groupes musculaires."""
    nom = request.form.get("nom", "").strip()
    if not nom:
        return None
    description = request.form.get("description", "").strip()
    groupe_principal = request.form.get("groupe_principal", "").strip()
    groupes = request.form.getlist("groupes_musculaires")
    return {
        "id": existing_id if existing_id is not None else next_id("exercice"),
        "nom": nom,
        "description": description,
        "groupe_principal": groupe_principal,
        "groupes_musculaires": groupes,
    }


@app.route("/exercices/<int:exercice_id>/modifier", methods=["GET", "POST"])
def exercice_modifier(exercice_id):
    exercice = find_by_id(EXERCICES, exercice_id)
    if not exercice:
        abort(404)
    if request.method == "POST":
        updated = _parse_exercice_form(request, existing_id=exercice_id)
        if updated:
            idx = next(i for i, e in enumerate(EXERCICES) if e["id"] == exercice_id)
            EXERCICES[idx] = updated
        return redirect(url_for("exercice_detail", exercice_id=exercice_id))
    return render_template("exercice_form.html", exercice=exercice, active_tab="exercices")


@app.route("/exercices/<int:exercice_id>/supprimer", methods=["POST"])
def exercice_supprimer(exercice_id):
    global EXERCICES
    EXERCICES = [e for e in EXERCICES if e["id"] != exercice_id]
    return redirect(url_for("exercices"))


# ── Export / Import ───────────────────────────────────────────

@app.route("/charger")
def charger_json():
    """Load coach_planner.json from the project root automatically."""
    global EXERCICES, SEANCES, PROGRAMMES
    json_path = os.path.join(os.path.dirname(__file__), "coach_planner.json")
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        EXERCICES  = data.get("exercices", [])
        SEANCES    = data.get("seances", [])
        PROGRAMMES = data.get("programmes", [])
        if "_next_ids" in data:
            _next_ids.update(data["_next_ids"])
        else:
            for kind, items in [("exercice", EXERCICES), ("seance", SEANCES), ("programme", PROGRAMMES)]:
                _next_ids[kind] = (max((i["id"] for i in items), default=0) + 1)
    except FileNotFoundError:
        pass
    return redirect(url_for("programmes"))


@app.route("/export")
def export_data():
    data = {
        "exercices": EXERCICES,
        "seances": SEANCES,
        "programmes": PROGRAMMES,
        "_next_ids": _next_ids,
    }
    buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    buf.seek(0)
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name="coach_planner.json")


@app.route("/import", methods=["POST"])
def import_data():
    global EXERCICES, SEANCES, PROGRAMMES
    f = request.files.get("fichier")
    if f:
        try:
            data = json.load(f)
            EXERCICES = data.get("exercices", [])
            SEANCES = data.get("seances", [])
            PROGRAMMES = data.get("programmes", [])
            if "_next_ids" in data:
                _next_ids.update(data["_next_ids"])
            else:
                for kind, items in [("exercice", EXERCICES), ("seance", SEANCES), ("programme", PROGRAMMES)]:
                    _next_ids[kind] = (max((i["id"] for i in items), default=0) + 1)
        except Exception:
            pass
    return redirect(url_for("programmes"))


if __name__ == "__main__":
    app.run(debug=True)
