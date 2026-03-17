import streamlit as st
import pandas as pd
from copy import deepcopy
import math
from collections import defaultdict

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Classix توزيع الأساتذة",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif; }
h1, h2, h3 { color: #0369a1 !important; font-weight: 700 !important; }

.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #6366f1);
    color: white !important; border: none; border-radius: 8px;
    font-family: 'Cairo', sans-serif; font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(14,165,233,0.4);
}
.metric-card {
    background: #f0f9ff; border: 1px solid #bae6fd;
    border-radius: 12px; padding: 1rem 1.5rem;
    text-align: center; margin-bottom: 8px;
}
.metric-card .value { font-size: 2rem; font-weight: 900; color: #0284c7; }
.metric-card .label { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
.section-header {
    background: linear-gradient(90deg, rgba(14,165,233,0.1), transparent);
    border-left: 4px solid #0ea5e9; padding: 0.75rem 1rem;
    border-radius: 0 8px 8px 0; margin-bottom: 1rem;
    font-size: 1.05rem; font-weight: 700; color: #1e293b;
}
.launch-box {
    background: linear-gradient(135deg, #f0fdf4, #f0f9ff);
    border: 2px solid #86efac; border-radius: 16px;
    padding: 2rem; text-align: center; margin: 1.5rem 0;
}
.launch-title { font-size: 1.4rem; font-weight: 900; color: #166534; margin-bottom: 0.5rem; }
.launch-sub   { font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem; }
.tag {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; margin: 2px;
}
.tag-blue   { background:#dbeafe; color:#1d4ed8; }
.tag-green  { background:#dcfce7; color:#15803d; }
.tag-gray   { background:#f1f5f9; color:#475569; }
.tag-red    { background:#fee2e2; color:#b91c1c; }
.tag-orange { background:#fff7ed; color:#c2410c; }
.result-row {
    display:flex; align-items:center; gap:12px; padding: 8px 12px;
    background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; margin-bottom:6px;
}
.stDataFrame { border-radius: 10px; overflow: hidden; }
.stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
MATIERES = ["العربية","الفرنسية","الانجليزية","الاجتماعيات","الرياضيات",
            "ع الحياة والارض","الفيزياء","الاسلاميات","التربية البدنية","الفلسفة","المعلوميات"]
BRANCHES = ["TC","1Bac","2Bac"]
MAX_HEURES   = 21
DECALAGE_MAX = 3

DEFAULT_NIVEAUX = {
    "TCSF":    {"label":"جذع مشترك علوم","branche":"TC",
                "matieres":{"العربية":2,"الفرنسية":6,"الانجليزية":3,"الاجتماعيات":2,"الرياضيات":5,"ع الحياة والارض":5,"الفيزياء":6,"الاسلاميات":2,"التربية البدنية":2,"الفلسفة":2,"المعلوميات":2}},
    "TCHL":    {"label":"جذع مشترك آداب","branche":"TC",
                "matieres":{"العربية":5,"الفرنسية":6,"الانجليزية":4,"الاجتماعيات":4,"الرياضيات":2,"ع الحياة والارض":2,"الفيزياء":0,"الاسلاميات":2,"التربية البدنية":2,"الفلسفة":2,"المعلوميات":2}},
    "1BAC-SEF":{"label":"1باك علوم","branche":"1Bac",
                "matieres":{"العربية":2,"الفرنسية":6,"الانجليزية":3,"الاجتماعيات":2,"الرياضيات":5,"ع الحياة والارض":6,"الفيزياء":6,"الاسلاميات":2,"التربية البدنية":2,"الفلسفة":2,"المعلوميات":0}},
    "1BAC-CHL":{"label":"1باك آداب","branche":"1Bac",
                "matieres":{"العربية":5,"الفرنسية":6,"الانجليزية":4,"الاجتماعيات":4,"الرياضيات":2,"ع الحياة والارض":2,"الفيزياء":0,"الاسلاميات":2,"التربية البدنية":2,"الفلسفة":2,"المعلوميات":0}},
    "2BAC-CPF":{"label":"2باك ع فيزيائية","branche":"2Bac",
                "matieres":{"العربية":2,"الفرنسية":4,"الانجليزية":3,"الاجتماعيات":0,"الرياضيات":5,"ع الحياة والارض":6,"الفيزياء":8,"الاسلاميات":1,"التربية البدنية":2,"الفلسفة":2,"المعلوميات":0}},
    "2BAC-SVT":{"label":"2باك ع ح أ","branche":"2Bac",
                "matieres":{"العربية":2,"الفرنسية":4,"الانجليزية":3,"الاجتماعيات":0,"الرياضيات":4,"ع الحياة والارض":8,"الفيزياء":4,"الاسلاميات":1,"التربية البدنية":2,"الفلسفة":2,"المعلوميات":0}},
    "2BAC-LF": {"label":"2باك آداب","branche":"2Bac",
                "matieres":{"العربية":5,"الفرنسية":4,"الانجليزية":5,"الاجتماعيات":4,"الرياضيات":2,"ع الحياة والارض":0,"الفيزياء":0,"الاسلاميات":2,"التربية البدنية":2,"الفلسفة":3,"المعلوميات":0}},
    "2BAC-CHL":{"label":"2باك إنسانية","branche":"2Bac",
                "matieres":{"العربية":4,"الفرنسية":4,"الانجليزية":4,"الاجتماعيات":5,"الرياضيات":2,"ع الحياة والارض":0,"الفيزياء":0,"الاسلاميات":3,"التربية البدنية":2,"الفلسفة":4,"المعلوميات":0}},
}

# ── Session state ──────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "niveaux":         deepcopy(DEFAULT_NIVEAUX),
        "niveaux_actifs":  list(DEFAULT_NIVEAUX.keys()),
        "nb_classes":      {k: 1 for k in DEFAULT_NIVEAUX},
        "nb_profs":        {m: 1 for m in MATIERES},
        "distribution":    {},
        "prof_config":     {},
        "dist_log":        [],
        "dist_cls":        {},
        "decalage_max":    DECALAGE_MAX,
        "max_heures_cfg":  MAX_HEURES,
        "manual_edits":    {},
        "expander_states": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_profs(matiere):
    return [f"{matiere}_{i+1}" for i in range(st.session_state.nb_profs.get(matiere, 1))]

def all_profs():
    r = []
    for m in MATIERES:
        r.extend(get_profs(m))
    return r

def heures_prof_matiere(prof_id, matiere):
    """Heures d'un prof pour une matière spécifique."""
    dist = st.session_state.distribution.get(prof_id, {})
    total = 0
    for niv_id, h in dist.items():
        if niv_id in st.session_state.niveaux_actifs:
            if st.session_state.niveaux[niv_id]["matieres"].get(matiere, 0) > 0:
                total += h
    return total

def heures_prof(prof_id):
    """Heures totales d'un prof (toutes matières)."""
    return sum(st.session_state.distribution.get(prof_id, {}).values())

def total_heures_needed(matiere):
    total = 0
    for niv_id in st.session_state.niveaux_actifs:
        niv = st.session_state.niveaux[niv_id]
        total += niv["matieres"].get(matiere, 0) * st.session_state.nb_classes.get(niv_id, 1)
    return total

def get_eligible_niveaux(prof_id, matiere):
    cfg         = st.session_state.prof_config.get(prof_id, {})
    branches_ok = cfg.get("branches", BRANCHES)
    niveaux_man = cfg.get("niveaux_manuels", [])
    actifs      = st.session_state.niveaux_actifs
    if niveaux_man:
        return [n for n in niveaux_man if n in actifs
                and st.session_state.niveaux[n]["matieres"].get(matiere, 0) > 0]
    return [n for n in actifs
            if st.session_state.niveaux[n]["branche"] in branches_ok
            and st.session_state.niveaux[n]["matieres"].get(matiere, 0) > 0]


# ══════════════════════════════════════════════════════════════════════════════
# ALGORITHME DE DISTRIBUTION AMÉLIORÉ
# ══════════════════════════════════════════════════════════════════════════════
def run_distribution():
    """
    RÈGLES FONDAMENTALES (ordre de priorité) :

    RÈGLE 1 — PRIORITÉ NIVEAU COMPLET
        Un prof doit IDÉALEMENT couvrir TOUTES les classes d'un même niveau
        avant de passer à d'autres niveaux/branches.
        → On commence par assigner les niveaux entiers à un seul prof.

    RÈGLE 2 — EXTENSION SI SOUS-CHARGÉ
        Si après attribution d'un niveau complet le prof est encore loin du plafond,
        on lui attribue :
          Option A : plusieurs classes d'un même niveau dans une AUTRE branche
          Option B : une classe de chaque niveau restant dans une autre branche
        On choisit l'option qui rapproche le plus de la moyenne.

    RÈGLE 3 — ÉQUILIBRE
        Chaque prof doit se rapprocher au maximum de la moyenne = total_h / n_profs.
        Le gap entre le max et le min des profs d'une matière ≤ decalage_max.

    RÈGLE 4 — INTÉGRITÉ
        Σ heures assignées = Σ heures requises (obligation stricte).
        Aucun prof à 0h.
        Aucun prof > max_h.
    """
    dec_max = st.session_state.decalage_max
    max_h   = st.session_state.get("max_heures_cfg", MAX_HEURES)

    # dist_cls[prof_id][niv_id] = nombre de classes entières attribuées
    dist_cls = {}
    log      = []

    def hpc(niv_id, mat):
        """Heures par classe pour un niveau et une matière."""
        return st.session_state.niveaux[niv_id]["matieres"].get(mat, 0)

    def ph(p, mat):
        """Heures actuelles d'un prof pour une matière."""
        return sum(
            dist_cls.get(p, {}).get(n, 0) * hpc(n, mat)
            for n in dist_cls.get(p, {})
        )

    def eligible(p, niv_id, mat):
        elig = get_eligible_niveaux(p, mat)
        return (not elig) or (niv_id in elig)

    for mat in MATIERES:
        profs = get_profs(mat)
        if not profs:
            continue
        n_profs = len(profs)
        for p in profs:
            dist_cls.setdefault(p, {})

        # ── Calcul des tâches : groupées par niveau ────────────────────────
        # niv_tasks[niv_id] = nombre total de classes disponibles pour ce niveau
        niv_tasks = {}
        for niv_id in st.session_state.niveaux_actifs:
            h  = hpc(niv_id, mat)
            nb = st.session_state.nb_classes.get(niv_id, 1)
            if h > 0 and nb > 0:
                niv_tasks[niv_id] = nb

        if not niv_tasks:
            continue

        total_h = sum(hpc(n, mat) * nb for n, nb in niv_tasks.items())
        target  = total_h / n_profs  # cible idéale par prof

        # ── ÉTAPE 1 : Attribution avec priorité NIVEAU COMPLET + majorité par branche ─
        #
        # RÈGLE FONDAMENTALE :
        #   Un prof peut enseigner tous les niveaux de toutes les branches.
        #   MAIS pour un niveau donné, il faut qu'UN SEUL prof couvre la MAJORITÉ
        #   (idéalement TOUTES) les classes de ce niveau.
        #   → On attribue d'abord les niveaux entiers à un seul prof.
        #   → Si le plafond empêche le niveau entier, on donne le maximum possible
        #     à un seul prof (plancher = ceil(nb_cls / 2) classes au même prof).
        #
        # EXTENSION après attribution d'un niveau complet :
        #   Si ph(prof) + h_niveau_suivant ≤ max_h  → on lui attribue aussi ce niveau
        #   (il consolide sa charge sur plusieurs niveaux de la même branche ou d'autres)
        #
        remaining = dict(niv_tasks)  # {niv_id: classes_restantes}

        # Trier par (nb_classes × h_par_classe) DESC : traiter les niveaux lourds en 1er
        sorted_niveaux = sorted(
            niv_tasks.keys(),
            key=lambda n: niv_tasks[n] * hpc(n, mat),
            reverse=True
        )

        def nb_classes_prof_has(p, niv_id):
            return dist_cls.get(p, {}).get(niv_id, 0)

        # Phase A : attribuer chaque niveau à UN SEUL prof (priorité majorité)
        for niv_id in sorted_niveaux:
            if remaining.get(niv_id, 0) <= 0:
                continue
            nb_cls  = remaining[niv_id]
            h_unit  = hpc(niv_id, mat)
            branche = st.session_state.niveaux[niv_id]["branche"]

            # Pool éligible
            pool = [p for p in profs if eligible(p, niv_id, mat)]
            if not pool:
                pool = profs

            # Préférer un prof qui a déjà des classes dans la même branche
            # → consolide la majorité dans la même branche
            def prof_score(p):
                # Heures déjà dans cette branche
                h_branch = sum(
                    dist_cls.get(p, {}).get(n, 0) * hpc(n, mat)
                    for n in dist_cls.get(p, {})
                    if st.session_state.niveaux.get(n, {}).get("branche") == branche
                )
                # Score : priorité à ceux qui ont déjà la branche ET sont sous la cible
                under_target = target - ph(p, mat)
                return (-h_branch, -under_target)  # minimiser → préférer branche existante + sous cible

            pool_sorted = sorted(pool, key=prof_score)

            # Chercher le premier prof qui peut absorber LE MAXIMUM de classes
            assigned = False
            for chosen in pool_sorted:
                h_available = max_h - ph(chosen, mat)
                max_cls_fit = int(h_available // h_unit)  # combien de classes tient dans le plafond
                if max_cls_fit <= 0:
                    continue
                cls_to_give = min(nb_cls, max_cls_fit)

                # Règle majorité : donner au moins ceil(nb_cls/2) classes au même prof
                # Si on ne peut même pas donner la majorité → passer au prof suivant
                majority_needed = math.ceil(nb_cls / 2)
                if cls_to_give < majority_needed and len(pool_sorted) > 1:
                    continue  # essayer le prof suivant

                dist_cls[chosen][niv_id] = dist_cls[chosen].get(niv_id, 0) + cls_to_give
                remaining[niv_id] = nb_cls - cls_to_give
                assigned = True
                break

            # Si aucun prof ne peut prendre la majorité, donner ce qu'on peut
            if not assigned:
                for chosen in pool_sorted:
                    h_available = max_h - ph(chosen, mat)
                    max_cls_fit = int(h_available // h_unit)
                    if max_cls_fit <= 0:
                        continue
                    cls_to_give = min(nb_cls, max_cls_fit)
                    dist_cls[chosen][niv_id] = dist_cls[chosen].get(niv_id, 0) + cls_to_give
                    remaining[niv_id] = nb_cls - cls_to_give
                    break

        # Phase B : classes résiduelles (celles que Phase A n'a pas pu placer entièrement)
        # On les distribue classe par classe au prof le moins chargé éligible
        for niv_id in sorted_niveaux:
            while remaining.get(niv_id, 0) > 0:
                h_unit  = hpc(niv_id, mat)
                branche = st.session_state.niveaux[niv_id]["branche"]
                pool    = [p for p in profs if eligible(p, niv_id, mat)]
                if not pool:
                    pool = profs

                under_cap = [p for p in pool if ph(p, mat) + h_unit <= max_h]
                active    = under_cap if under_cap else pool

                if not active:
                    log.append(f"❌ {mat} / {niv_id}: impossible d'assigner — plafond atteint pour tous les profs")
                    remaining[niv_id] -= 1
                    continue

                # Préférer le prof qui a déjà ce niveau (consolide le niveau)
                # puis celui qui a la même branche, puis le moins chargé
                def score_residual(p):
                    has_niv    = dist_cls.get(p, {}).get(niv_id, 0)
                    h_branch   = sum(
                        dist_cls.get(p, {}).get(n, 0) * hpc(n, mat)
                        for n in dist_cls.get(p, {})
                        if st.session_state.niveaux.get(n, {}).get("branche") == branche
                    )
                    return (-has_niv, -h_branch, ph(p, mat) - target)

                chosen = min(active, key=score_residual)
                dist_cls[chosen][niv_id] = dist_cls[chosen].get(niv_id, 0) + 1
                remaining[niv_id] -= 1

        # ── ÉTAPE 2 : Garantir qu'aucun prof n'a 0 heure ──────────────────
        for _it in range(n_profs * 10):
            zeros = [p for p in profs if ph(p, mat) == 0]
            if not zeros:
                break
            zp = zeros[0]

            donors = sorted(
                [p for p in profs if p != zp and ph(p, mat) > 0],
                key=lambda p: ph(p, mat), reverse=True
            )
            done = False
            for donor in donors:
                donor_niveaux = sorted(
                    [(n, hpc(n, mat), dist_cls[donor].get(n, 0))
                     for n in dist_cls.get(donor, {})
                     if dist_cls[donor].get(n, 0) > 0 and hpc(n, mat) > 0],
                    key=lambda x: x[1]
                )
                for niv_id, h_u, nb_assigned in donor_niveaux:
                    if not eligible(zp, niv_id, mat):
                        continue
                    if ph(zp, mat) + h_u > max_h:
                        continue
                    # Transfert d'UNE classe
                    dist_cls[donor][niv_id] -= 1
                    if dist_cls[donor][niv_id] == 0:
                        del dist_cls[donor][niv_id]
                    dist_cls[zp][niv_id] = dist_cls[zp].get(niv_id, 0) + 1
                    log.append(
                        f"🔄 {mat}: نقل قسم {niv_id}({h_u}h) "
                        f"من أستاذ {donor.split('_')[-1]} → أستاذ {zp.split('_')[-1]}"
                    )
                    done = True
                    break
                if done:
                    break
            if not done:
                log.append(
                    f"❌ {mat}: أستاذ {zp.split('_')[-1]} لا يمكن إسناده — "
                    f"تحقق من إعدادات الشعب والمستويات"
                )
                break

        # ── ÉTAPE 3 : Rééquilibrage fin pour respecter dec_max ET la cible ──
        # On fait plusieurs passes de rééquilibrage pour converger vers la moyenne
        improved = True
        iters    = 0
        while improved and iters < 1000:
            improved = False
            iters   += 1
            h_vals   = [ph(p, mat) for p in profs]
            cur_gap  = max(h_vals) - min(h_vals)
            if cur_gap <= dec_max:
                break

            max_p  = max(profs, key=lambda p: ph(p, mat))
            min_ps = [p for p in profs if ph(p, mat) < ph(max_p, mat)]
            if not min_ps:
                break
            min_p = min(min_ps, key=lambda p: ph(p, mat))

            # Chercher la classe à transférer qui minimise le gap résultant
            best_transfer  = None
            best_gap_after = cur_gap

            candidates = [
                (n, hpc(n, mat))
                for n, c in dist_cls.get(max_p, {}).items()
                if c > 0 and hpc(n, mat) > 0
            ]
            # Trier : on essaie d'abord les classes dont h ≈ (ph(max_p) - ph(min_p)) / 2
            ideal_transfer = (ph(max_p, mat) - ph(min_p, mat)) / 2
            candidates.sort(key=lambda x: abs(x[1] - ideal_transfer))

            for niv_id, h_u in candidates:
                if not eligible(min_p, niv_id, mat):
                    continue
                if ph(min_p, mat) + h_u > max_h:
                    continue
                new_max_h  = ph(max_p, mat) - h_u
                new_min_h  = ph(min_p, mat) + h_u
                new_gap    = new_max_h - new_min_h
                # Accepter le transfert seulement si ça améliore le gap
                if new_gap < best_gap_after:
                    best_gap_after = new_gap
                    best_transfer  = (niv_id, h_u)

            if best_transfer:
                niv_id, h_u = best_transfer
                dist_cls[max_p][niv_id] -= 1
                if dist_cls[max_p][niv_id] == 0:
                    del dist_cls[max_p][niv_id]
                dist_cls[min_p][niv_id] = dist_cls[min_p].get(niv_id, 0) + 1
                improved = True

        # Rapport final
        h_vals    = [ph(p, mat) for p in profs]
        final_gap = max(h_vals) - min(h_vals) if h_vals else 0
        if final_gap > dec_max:
            log.append(
                f"⚠️ {mat}: الفجوة النهائية {final_gap}h > {dec_max}h — "
                f"قيود الشعب/المستويات تمنع التوازن الكامل"
            )

    # ── Conversion dist_cls → dist_hours ──────────────────────────────────────
    dist_hours = {}
    for mat in MATIERES:
        for p in get_profs(mat):
            dist_hours.setdefault(p, {})
            for niv_id, nb_cls in dist_cls.get(p, {}).items():
                h = hpc(niv_id, mat)
                if nb_cls > 0 and h > 0:
                    key_exists = dist_hours[p].get(niv_id, 0)
                    dist_hours[p][niv_id] = key_exists + nb_cls * h

    # ── Vérification d'intégrité ───────────────────────────────────────────────
    for mat in MATIERES:
        needed   = total_heures_needed(mat)
        assigned = sum(
            sum(
                dist_cls.get(p, {}).get(n, 0) * hpc(n, mat)
                for n in st.session_state.niveaux_actifs
                if hpc(n, mat) > 0
            )
            for p in get_profs(mat)
        )
        if needed > 0 and assigned != needed:
            log.append(f"⚠️ {mat}: موزع {assigned}h ≠ مطلوب {needed}h")

    st.session_state.distribution = dist_hours
    st.session_state.dist_cls     = dist_cls
    st.session_state.dist_log     = log
    # Réinitialiser les éditions manuelles après une nouvelle distribution
    st.session_state.manual_edits = {}
    return log


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎓 CLASSIX : ابن خلدون التأهيلية")
    st.markdown("---")
    page = st.radio("", [
        "⚙️ الإعدادات",
        "👥 الأساتذة وتخصيصاتهم",
        "🚀 تشغيل التوزيع",
        "📋 النتائج",
    ], label_visibility="collapsed")
    st.markdown("---")
    total_profs_count = sum(st.session_state.nb_profs.values())
    total_niv_count   = len(st.session_state.niveaux_actifs)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='value'>{total_profs_count}</div>
        <div class='label'>إجمالي الأساتذة</div>
    </div>
    <div class='metric-card'>
        <div class='value'>{total_niv_count}</div>
        <div class='label'>المستويات النشطة</div>
    </div>""", unsafe_allow_html=True)
    if st.session_state.distribution:
        nonzero = [heures_prof(p) for p in all_profs() if heures_prof(p) > 0]
        if nonzero:
            avg_h = sum(nonzero) / len(nonzero)
            st.markdown(f"""
            <div class='metric-card' style='margin-top:8px'>
                <div class='value' style='font-size:1.5rem'>{avg_h:.1f}h</div>
                <div class='label'>متوسط الحمل</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
if page == "⚙️ الإعدادات":
    st.markdown("# ⚙️ إعدادات المؤسسة")
    tab1, tab2, tab3, tab4 = st.tabs(["📚 المستويات النشطة", "🏫 عدد الأقسام", "📖 ساعات المواد", "⚖️ معاملات التوزيع"])

    with tab1:
        st.markdown("<div class='section-header'>اختر المستويات المتوفرة في مؤسستك</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i, branche in enumerate(BRANCHES):
            with cols[i]:
                st.markdown(f"**{branche}**")
                for niv_id, niv in DEFAULT_NIVEAUX.items():
                    if niv["branche"] != branche:
                        continue
                    checked = niv_id in st.session_state.niveaux_actifs
                    new_val = st.checkbox(f"{niv_id} — {niv['label']}", value=checked, key=f"actif_{niv_id}")
                    if new_val and niv_id not in st.session_state.niveaux_actifs:
                        st.session_state.niveaux_actifs.append(niv_id)
                    elif not new_val and niv_id in st.session_state.niveaux_actifs:
                        st.session_state.niveaux_actifs.remove(niv_id)

    with tab2:
        st.markdown("<div class='section-header'>عدد الأقسام لكل مستوى</div>", unsafe_allow_html=True)
        # Sync: si la clé widget n'existe pas encore, on l'initialise depuis nb_classes
        # Cela garantit que la valeur affichée = la valeur sauvegardée, SANS écraser
        # ce que l'utilisateur a tapé entre deux navigations.
        for niv_id in st.session_state.nb_classes:
            wkey = f"cls_{niv_id}"
            if wkey not in st.session_state:
                st.session_state[wkey] = st.session_state.nb_classes.get(niv_id, 1)

        def _save_cls(niv_id):
            st.session_state.nb_classes[niv_id] = st.session_state[f"cls_{niv_id}"]

        cols = st.columns(3)
        for i, branche in enumerate(BRANCHES):
            with cols[i]:
                st.markdown(f"**{branche}**")
                for niv_id in [k for k, v in st.session_state.niveaux.items()
                               if v["branche"] == branche and k in st.session_state.niveaux_actifs]:
                    niv = st.session_state.niveaux[niv_id]
                    st.number_input(
                        niv["label"], min_value=0, max_value=20,
                        key=f"cls_{niv_id}",
                        on_change=_save_cls, args=(niv_id,)
                    )

    with tab3:
        st.markdown("<div class='section-header'>ساعات كل مادة بكل مستوى (قابلة للتعديل)</div>", unsafe_allow_html=True)
        actifs = st.session_state.niveaux_actifs
        if not actifs:
            st.warning("لا توجد مستويات نشطة")
        else:
            # Sync: initialiser les clés widget depuis niveaux si elles n'existent pas
            for niv_id in actifs:
                for mat in MATIERES:
                    wkey = f"h_{niv_id}_{mat}"
                    if wkey not in st.session_state:
                        st.session_state[wkey] = st.session_state.niveaux[niv_id]["matieres"].get(mat, 0)

            def _save_h(niv_id, mat):
                st.session_state.niveaux[niv_id]["matieres"][mat] = st.session_state[f"h_{niv_id}_{mat}"]

            for niv_id in actifs:
                niv = st.session_state.niveaux[niv_id]
                with st.expander(f"📝 {niv_id} — {niv['label']}"):
                    c1, c2, c3 = st.columns(3)
                    for j, mat in enumerate(MATIERES):
                        with [c1, c2, c3][j % 3]:
                            st.number_input(
                                mat, min_value=0, max_value=30,
                                key=f"h_{niv_id}_{mat}",
                                on_change=_save_h, args=(niv_id, mat)
                            )
            st.markdown("---")
            st.markdown("**ملخص الساعات:**")
            disp = {
                st.session_state.niveaux[n]["label"]: {m: st.session_state.niveaux[n]["matieres"].get(m, 0) for m in MATIERES}
                for n in actifs
            }
            st.dataframe(pd.DataFrame(disp, index=MATIERES), use_container_width=True)

    with tab4:
        st.markdown("<div class='section-header'>⚖️ معاملات التوزيع التلقائي</div>", unsafe_allow_html=True)

        # نفس النمط المستخدم في tab2 و tab3:
        # - نُهيّئ مفتاح الـ widget مرة واحدة فقط إذا لم يكن موجوداً
        # - نستخدم on_change لكتابة القيمة فوراً في session_state
        # - لا نستخدم value= أبداً لأنه يعيد تعيين القيمة عند كل render
        if "max_heures_cfg" not in st.session_state:
            st.session_state["max_heures_cfg"] = MAX_HEURES
        if "decalage_max" not in st.session_state:
            st.session_state["decalage_max"] = DECALAGE_MAX

        def _save_max():
            st.session_state.max_heures_cfg = st.session_state["_w_max_heures"]

        def _save_dec():
            st.session_state.decalage_max = st.session_state["_w_decalage"]

        # initialiser les clés widget UNE SEULE FOIS depuis les valeurs sauvegardées
        if "_w_max_heures" not in st.session_state:
            st.session_state["_w_max_heures"] = st.session_state.max_heures_cfg
        if "_w_decalage" not in st.session_state:
            st.session_state["_w_decalage"] = st.session_state.decalage_max

        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            st.markdown("##### الحد الأقصى للساعات الأسبوعية / أستاذ")
            st.number_input(
                "الحد الأقصى (ساعة/أسبوع)",
                min_value=10, max_value=35,
                key="_w_max_heures",
                on_change=_save_max,
                help="لا يمكن لأي أستاذ تجاوز هذا العدد من الساعات في الأسبوع"
            )
        with col_cfg2:
            st.markdown("##### الفارق الأقصى المسموح بين أساتذة نفس المادة")
            st.number_input(
                "الفارق الأقصى (ساعة)",
                min_value=0, max_value=10,
                key="_w_decalage",
                on_change=_save_dec,
                help="الفرق الأقصى المسموح بين أساتذة نفس المادة"
            )
            cur_dec   = st.session_state.decalage_max
            label_dec = "توازن ممتاز" if cur_dec <= 3 else "مقبول" if cur_dec <= 6 else "فجوة كبيرة"
            st.info(f"الفارق المسموح: **{cur_dec}h** — {label_dec}")

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"<div class='metric-card'>"
                f"<div class='value'>{st.session_state.max_heures_cfg}h</div>"
                f"<div class='label'>الحد الأقصى/أستاذ</div>"
                f"</div>", unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"<div class='metric-card'>"
                f"<div class='value'>{st.session_state.decalage_max}h</div>"
                f"<div class='label'>الفارق الأقصى المسموح</div>"
                f"</div>", unsafe_allow_html=True
            )
        with c3:
            total_needed = sum(total_heures_needed(m) for m in MATIERES)
            st.markdown(
                f"<div class='metric-card'>"
                f"<div class='value'>{total_needed}h</div>"
                f"<div class='label'>إجمالي الساعات المطلوبة</div>"
                f"</div>", unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — PROFESSEURS & CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 الأساتذة وتخصيصاتهم":
    st.markdown("# 👥 الأساتذة وتخصيصاتهم")
    tab1, tab2 = st.tabs(["🔢 عدد الأساتذة لكل مادة", "🎯 تخصيص الشعب والمستويات"])

    with tab1:
        st.markdown("<div class='section-header'>حدد عدد الأساتذة لكل مادة</div>", unsafe_allow_html=True)
        st.caption("💡 الحد الأقصى لكل أستاذ هو 21 ساعة/أسبوع — يُحسب العدد المقترح تلقائياً")
        cols = st.columns(3)
        for i, mat in enumerate(MATIERES):
            with cols[i % 3]:
                needed    = total_heures_needed(mat)
                suggested = max(1, math.ceil(needed / MAX_HEURES))
                val = st.number_input(
                    mat, min_value=1, max_value=20,
                    value=st.session_state.nb_profs.get(mat, 1),
                    key=f"np_{mat}",
                    help=f"الساعات المطلوبة: {needed}h | مقترح: {suggested} أستاذ"
                )
                st.session_state.nb_profs[mat] = val
                if needed > 0:
                    avg    = needed / val
                    floor_ = int(needed // val)
                    extra  = needed - floor_ * val
                    icon   = "🔴" if avg > MAX_HEURES else "🟢" if avg >= 15 else "🟡"
                    ideal_str = (
                        f"{floor_}h × {val - int(extra)} + {floor_+1}h × {int(extra)}"
                        if extra else f"{floor_}h × {val}"
                    )
                    st.caption(f"{icon} {needed}h ÷ {val} = **{avg:.1f}h/أستاذ** | مثالي: {ideal_str}")

    with tab2:
        st.markdown("<div class='section-header'>تخصيص كل أستاذ — الشعب المسموحة والمستويات</div>", unsafe_allow_html=True)
        st.info("📌 كل أستاذ يمكن أن يُغطي أكثر من شعبة. يمكنك تحديد مستويات بعينها أو تركها فارغة للسماح بكل المستويات.")

        sel_mat = st.selectbox("اختر المادة لتخصيص أساتذتها", MATIERES, key="sel_mat_cfg")
        profs   = get_profs(sel_mat)

        needed_sel   = total_heures_needed(sel_mat)
        nb_profs_sel = len(profs)
        target_sel   = needed_sel / nb_profs_sel if nb_profs_sel else 0
        floor_sel    = int(needed_sel // nb_profs_sel) if nb_profs_sel else 0
        extra_sel    = needed_sel - floor_sel * nb_profs_sel if nb_profs_sel else 0
        dec_disp     = st.session_state.decalage_max
        dist_ideal_str = (
            f"{floor_sel}h × {nb_profs_sel - int(extra_sel)} + {floor_sel+1}h × {int(extra_sel)} أستاذ"
            if extra_sel else f"{floor_sel}h × {nb_profs_sel} أستاذ"
        )

        col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
        col_i1.metric("إجمالي ساعات " + sel_mat, f"{needed_sel}h")
        col_i2.metric("عدد الأساتذة", str(nb_profs_sel))
        col_i3.metric("المعدل المستهدف", f"{target_sel:.1f}h")
        col_i4.metric("التوزيع المثالي", dist_ideal_str)
        col_i5.metric("الفارق الأقصى المسموح", f"{dec_disp}h")
        st.divider()

        for prof_id in profs:
            cfg = st.session_state.prof_config.get(prof_id, {})
            h_mat  = heures_prof_matiere(prof_id, sel_mat) if st.session_state.distribution else 0
            diff_t = h_mat - target_sel
            hcolor = "🟢" if abs(diff_t) <= dec_disp else "🔴"
            lbl_diff = f"  {diff_t:+.0f}h vs معدل" if st.session_state.distribution else ""

            with st.expander(
                f"👤 أستاذ {prof_id.split('_')[-1]}  —  {sel_mat}  |  {h_mat}h{lbl_diff}  {hcolor if st.session_state.distribution else ''}"
            ):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**الشعب المسموحة**")
                    current_branches = cfg.get("branches", [])
                    default_br       = [b for b in current_branches if b in BRANCHES]
                    sel_branches = st.multiselect(
                        "الشعب", BRANCHES,
                        default=default_br,
                        key=f"br_{prof_id}",
                        label_visibility="collapsed"
                    )
                with col_b:
                    allowed_br  = sel_branches if sel_branches else BRANCHES
                    niv_options = [
                        k for k in st.session_state.niveaux_actifs
                        if st.session_state.niveaux[k]["branche"] in allowed_br
                        and st.session_state.niveaux[k]["matieres"].get(sel_mat, 0) > 0
                    ]
                    current_man = [n for n in cfg.get("niveaux_manuels", []) if n in niv_options]
                    st.markdown("**تحديد مستويات بعينها** (اختياري)")
                    sel_niveaux = st.multiselect(
                        "المستويات", niv_options, default=current_man,
                        key=f"nv_{prof_id}", label_visibility="collapsed",
                        format_func=lambda x: f"{x} — {st.session_state.niveaux[x]['label']}"
                    )

                st.session_state.prof_config[prof_id] = {
                    "branches":        sel_branches if sel_branches else BRANCHES,
                    "niveaux_manuels": sel_niveaux
                }

                b_html = "".join([f"<span class='tag tag-blue'>{b}</span>" for b in (sel_branches or BRANCHES)])
                n_html = (
                    "".join([f"<span class='tag tag-green'>{n}</span>" for n in sel_niveaux])
                    if sel_niveaux else "<span class='tag tag-gray'>جميع المستويات</span>"
                )
                st.markdown(f"**الشعب:** {b_html} &nbsp;&nbsp; **المستويات:** {n_html}", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — LANCER LA RÉPARTITION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚀 تشغيل التوزيع":
    st.markdown("# 🚀 تشغيل التوزيع")

    warnings_pre = []
    for mat in MATIERES:
        needed = total_heures_needed(mat)
        nb     = st.session_state.nb_profs.get(mat, 1)
        if needed > 0 and nb * st.session_state.max_heures_cfg < needed:
            warnings_pre.append(f"**{mat}**: {needed}h مطلوبة — {nb} أستاذ × {st.session_state.max_heures_cfg}h = {nb*st.session_state.max_heures_cfg}h فقط")

    if warnings_pre:
        st.warning("⚠️ **تنبيه:** عدد الأساتذة قد لا يكفي لهذه المواد:")
        for w in warnings_pre:
            st.markdown(f"- {w}")
        st.markdown("---")

    st.markdown("<div class='section-header'>ملخص ما سيتم توزيعه</div>", unsafe_allow_html=True)
    rows_prev = []
    for mat in MATIERES:
        needed = total_heures_needed(mat)
        if needed == 0:
            continue
        nb  = st.session_state.nb_profs.get(mat, 1)
        avg = needed / nb if nb else 0
        rows_prev.append({
            "المادة":         mat,
            "إجمالي الساعات": needed,
            "عدد الأساتذة":   nb,
            "المعدل المتوقع": f"{avg:.1f}h",
            "الحالة":         "✅ مناسب" if avg <= st.session_state.max_heures_cfg else "🔴 تجاوز"
        })
    if rows_prev:
        st.dataframe(pd.DataFrame(rows_prev), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("""
    <div class='launch-box'>
        <div class='launch-title'>🎯 جاهز لتشغيل التوزيع التلقائي</div>
        <div class='launch-sub'>
            سيتم توزيع الحصص بشكل متوازن بين الأساتذة<br>
            مع احترام الحد الأقصى للساعات وتخصيصات كل أستاذ<br>
            <strong>الأولوية: يغطي كل أستاذ جميع أقسام نفس المستوى قبل الانتقال لمستوى آخر</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🚀 تشغيل التوزيع الآن", use_container_width=True):
            with st.spinner("جارٍ توزيع الحصص..."):
                log = run_distribution()
            st.success("✅ تم التوزيع بنجاح! انتقل إلى صفحة **📋 النتائج** لعرض التفاصيل.")
            if log:
                st.warning("بعض الملاحظات أثناء التوزيع:")
                for l in log:
                    st.markdown(f"- {l}")

    st.markdown("---")

    # ── ÉDITION MANUELLE — FIX : utiliser un formulaire pour éviter le rerun ──
    if st.session_state.distribution:
        st.markdown("<div class='section-header'>✏️ تعديل يدوي بعد التوزيع</div>", unsafe_allow_html=True)
        st.caption("يمكنك تعديل قيم التوزيع يدوياً لكل أستاذ ومستوى — اضغط 'حفظ التعديلات' لتطبيقها")

        sel_mat_m = st.selectbox("اختر المادة للتعديل", MATIERES, key="man_mat")
        profs_m   = get_profs(sel_mat_m)
        niv_mat   = [k for k in st.session_state.niveaux_actifs
                     if st.session_state.niveaux[k]["matieres"].get(sel_mat_m, 0) > 0]

        if not niv_mat:
            st.info("لا توجد مستويات لهذه المادة")
        else:
            needed_m  = total_heures_needed(sel_mat_m)
            nb_m      = len(profs_m)
            target_m  = needed_m / nb_m if nb_m else 0
            max_h_cfg = st.session_state.max_heures_cfg

            # Initialiser les éditions manuelles pour cette matière si absent
            edit_key = f"edits_{sel_mat_m}"
            if edit_key not in st.session_state.manual_edits:
                st.session_state.manual_edits[edit_key] = {}
                for prof_id in profs_m:
                    dist = st.session_state.distribution.get(prof_id, {})
                    st.session_state.manual_edits[edit_key][prof_id] = {
                        niv_id: int(dist.get(niv_id, 0))
                        for niv_id in niv_mat
                    }

            # FIX : Utiliser st.form pour éviter les reruns à chaque modification
            # L'expander reste ouvert car le rerun n'est déclenché qu'au submit
            with st.form(key=f"form_edit_{sel_mat_m}"):
                st.markdown(f"**تعديل توزيع مادة: {sel_mat_m}**")

                for prof_id in profs_m:
                    dist   = st.session_state.distribution.get(prof_id, {})
                    h_mat  = heures_prof_matiere(prof_id, sel_mat_m)
                    diff_t = h_mat - target_m
                    icon   = "🟢" if abs(diff_t) <= st.session_state.decalage_max else "🔴"

                    st.markdown(
                        f"**👤 أستاذ {prof_id.split('_')[-1]}** — "
                        f"{h_mat}h ({diff_t:+.0f}h vs معدل {target_m:.1f}h) {icon}"
                    )

                    sub_cols = st.columns(min(4, len(niv_mat)))
                    for j, niv_id in enumerate(niv_mat):
                        niv   = st.session_state.niveaux[niv_id]
                        h_max = int(
                            niv["matieres"].get(sel_mat_m, 0) *
                            st.session_state.nb_classes.get(niv_id, 1)
                        )
                        cur = int(dist.get(niv_id, 0))
                        with sub_cols[j % len(sub_cols)]:
                            st.number_input(
                                niv["label"],
                                min_value=0,
                                max_value=h_max,
                                value=cur,
                                key=f"form_man_{prof_id}_{niv_id}",
                                help=f"Max: {h_max}h"
                            )
                    st.divider()

                submitted = st.form_submit_button("💾 حفظ التعديلات", use_container_width=True)
                if submitted:
                    # Appliquer les modifications
                    for prof_id in profs_m:
                        dist = st.session_state.distribution.setdefault(prof_id, {})
                        for niv_id in niv_mat:
                            new_val = st.session_state[f"form_man_{prof_id}_{niv_id}"]
                            dist[niv_id] = new_val
                        # Nettoyer les zéros
                        keys_to_del = [k for k, v in dist.items() if v == 0]
                        for k in keys_to_del:
                            del dist[k]
                    # Invalider le cache des éditions pour recalcul
                    if edit_key in st.session_state.manual_edits:
                        del st.session_state.manual_edits[edit_key]
                    st.success("✅ تم حفظ التعديلات بنجاح!")
                    st.rerun()

            # Vérification totale pour cette matière
            total_assigned_m = sum(
                heures_prof_matiere(p, sel_mat_m) for p in profs_m
            )
            diff_check = total_assigned_m - needed_m
            check_color = "#f0fdf4" if diff_check == 0 else "#fef2f2"
            check_border = "#86efac" if diff_check == 0 else "#fca5a5"
            check_icon  = "✅" if diff_check == 0 else "❌"
            st.markdown(
                f"""<div style="background:{check_color};border:2px solid {check_border};
                border-radius:10px;padding:12px 16px;margin-top:8px">
                {check_icon} إجمالي الساعات المعدّلة: <strong>{total_assigned_m}h</strong>
                / المطلوب: <strong>{needed_m}h</strong>
                {'— مطابق ✅' if diff_check == 0 else f'— فارق {diff_check:+d}h ❌'}
                </div>""",
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — RÉSULTATS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 النتائج":
    st.markdown("# 📋 النتائج والملخص")

    if not st.session_state.distribution:
        st.warning("⚠️ لم يتم تشغيل التوزيع بعد. انتقل إلى صفحة **🚀 تشغيل التوزيع**")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["👥 ملخص الأساتذة", "📚 ملخص المواد", "📊 إحصائيات وتصدير"])

    with tab1:
        st.markdown("<div class='section-header'>حصص كل أستاذ — تفاصيل التوزيع</div>", unsafe_allow_html=True)
        filter_mat = st.selectbox("تصفية حسب المادة", ["الكل"] + MATIERES, key="flt_res")
        mats_show  = MATIERES if filter_mat == "الكل" else [filter_mat]

        for mat in mats_show:
            needed  = total_heures_needed(mat)
            n_profs = st.session_state.nb_profs.get(mat, 1)
            target  = needed / n_profs if n_profs else 0
            rows    = []

            for p in get_profs(mat):
                dist      = st.session_state.distribution.get(p, {})
                h_mat     = heures_prof_matiere(p, mat)
                diff_target = h_mat - target

                # Détails par niveau : X classes du niveau Y dans la branche Z
                niv_details = []
                for niv_id, h_val in dist.items():
                    if h_val <= 0 or niv_id not in st.session_state.niveaux_actifs:
                        continue
                    niv     = st.session_state.niveaux[niv_id]
                    h_unit  = niv["matieres"].get(mat, 0)
                    if h_unit <= 0:
                        continue
                    nb_cls  = h_val // h_unit
                    branche = niv["branche"]
                    label   = niv["label"]
                    niv_details.append(
                        f"{nb_cls} قسم من {label} ({branche}) = {h_val}h"
                    )

                rows.append({
                    "الأستاذ":             f"أستاذ {p.split('_')[-1]}",
                    "ساعات المادة":        h_mat,
                    "الهدف (المعدل)":      f"{target:.1f}h",
                    "الفرق عن المعدل":     f"{diff_target:+.1f}h",
                    "تفاصيل الأقسام":      " | ".join(niv_details) if niv_details else "—",
                    "الحالة": (
                        "🔴 تجاوز الحد" if h_mat > st.session_state.max_heures_cfg
                        else "❌ لم يُسند" if h_mat == 0
                        else "🟢 جيد" if abs(diff_target) <= st.session_state.decalage_max
                        else "🟡 قريب"
                    ),
                })

            if rows:
                total_assigned = sum(r["ساعات المادة"] for r in rows)
                rows.append({
                    "الأستاذ":            "📊 المجموع",
                    "ساعات المادة":       total_assigned,
                    "الهدف (المعدل)":     f"المطلوب: {needed}h",
                    "الفرق عن المعدل":    ("✅ = " if total_assigned == needed else f"❌ فارق {total_assigned-needed:+d}h"),
                    "تفاصيل الأقسام":     "",
                    "الحالة":             ("✅ مطابق" if total_assigned == needed else "❌ خطأ"),
                })
                st.markdown(f"#### 📖 {mat}  —  المطلوب: **{needed}h**  |  المعدل: **{target:.1f}h/أستاذ**")
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("<div class='section-header'>مقارنة الساعات المطلوبة والموزعة</div>", unsafe_allow_html=True)
        st.info("✅ **قاعدة التحقق:** مجموع ساعات أساتذة كل مادة يجب أن يساوي تماماً إجمالي ساعات تلك المادة")

        rows = []
        total_needed_all   = 0
        total_assigned_all = 0

        for mat in MATIERES:
            needed   = total_heures_needed(mat)
            assigned = sum(heures_prof_matiere(p, mat) for p in get_profs(mat))
            diff     = assigned - needed
            total_needed_all   += needed
            total_assigned_all += assigned
            rows.append({
                "المادة":           mat,
                "الساعات المطلوبة": needed,
                "الساعات الموزعة":  assigned,
                "الفرق":            diff,
                "عدد الأساتذة":     st.session_state.nb_profs.get(mat, 1),
                "الحالة": (
                    "✅ متوازن" if diff == 0
                    else f"➕ زيادة {diff}h" if diff > 0
                    else f"➖ نقص {abs(diff)}h"
                ),
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        diff_total = total_assigned_all - total_needed_all
        box_color  = "#f0fdf4" if diff_total == 0 else "#fef2f2"
        brd_color  = "#86efac" if diff_total == 0 else "#fca5a5"
        icon_tot   = "✅" if diff_total == 0 else "❌"
        msg_tot    = "التوزيع مكتمل — كل الساعات موزعة بشكل صحيح" if diff_total == 0 else f"تحذير: فارق {abs(diff_total)}h بين الساعات المطلوبة والموزعة"
        st.markdown(f"""
        <div style="background:{box_color};border:2px solid {brd_color};border-radius:12px;padding:16px 20px;margin-top:8px">
            <div style="font-size:1.1rem;font-weight:800;color:#1e293b;margin-bottom:8px">{icon_tot} التحقق الإجمالي</div>
            <div style="display:flex;gap:32px;flex-wrap:wrap">
                <div><span style="color:#64748b;font-size:0.85rem">إجمالي الساعات المطلوبة</span><br>
                     <span style="font-size:1.4rem;font-weight:900;color:#0284c7">{total_needed_all}h</span></div>
                <div><span style="color:#64748b;font-size:0.85rem">إجمالي الساعات الموزعة</span><br>
                     <span style="font-size:1.4rem;font-weight:900;color:#16a34a">{total_assigned_all}h</span></div>
                <div><span style="color:#64748b;font-size:0.85rem">الفارق</span><br>
                     <span style="font-size:1.4rem;font-weight:900;color:{'#16a34a' if diff_total==0 else '#dc2626'}">{diff_total:+d}h</span></div>
            </div>
            <div style="margin-top:10px;color:#475569;font-size:0.9rem">{msg_tot}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        all_h    = [heures_prof(p) for p in all_profs()]
        nonzero  = [h for h in all_h if h > 0]
        avg_kpi  = sum(nonzero) / len(nonzero) if nonzero else 0
        max_h_c  = st.session_state.max_heures_cfg
        over_kpi = sum(1 for h in all_h if h > max_h_c)
        low_kpi  = sum(1 for h in all_h if 0 < h < 12)

        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl, color in [
            (c1, sum(st.session_state.nb_profs.values()), "إجمالي الأساتذة", "#0284c7"),
            (c2, f"{avg_kpi:.1f}h", "متوسط الحمل", "#0284c7"),
            (c3, over_kpi, "تجاوزوا الحد", "#dc2626"),
            (c4, low_kpi, "حمل منخفض (<12h)", "#d97706"),
        ]:
            with col:
                col.markdown(f"""<div class='metric-card'>
                    <div class='value' style='color:{color}'>{val}</div>
                    <div class='label'>{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📊 الحمل الأسبوعي لكل أستاذ (حسب المادة)")
        for mat in MATIERES:
            profs_m = get_profs(mat)
            if not any(heures_prof_matiere(p, mat) > 0 for p in profs_m):
                continue
            st.markdown(f"**{mat}**")
            for p in profs_m:
                h   = heures_prof_matiere(p, mat)
                pct = min(h / max_h_c * 100, 100)
                col = "#16a34a" if h <= max_h_c else "#dc2626"
                lbl = p.split("_")[-1]
                st.markdown(f"""
                <div class='result-row'>
                    <span style="min-width:70px;color:#475569;font-size:0.85rem">أستاذ {lbl}</span>
                    <div style="flex:1;height:12px;background:#e2e8f0;border-radius:6px;overflow:hidden">
                        <div style="width:{pct}%;height:100%;background:{col};border-radius:6px"></div>
                    </div>
                    <span style="min-width:55px;text-align:right;color:{col};font-weight:700;font-size:0.9rem">{h}h</span>
                    <span style="color:#94a3b8;font-size:0.75rem">/ {max_h_c}h</span>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### ⚖️ تحليل التوازن بين الأساتذة")
        for mat in MATIERES:
            profs_m = get_profs(mat)
            hours_m = [heures_prof_matiere(p, mat) for p in profs_m]
            if not any(h > 0 for h in hours_m):
                continue
            min_h = min(hours_m)
            max_hm = max(hours_m)
            gap    = max_hm - min_h
            dec    = st.session_state.decalage_max
            needed_m = total_heures_needed(mat)
            target_m = needed_m / len(profs_m) if profs_m else 0
            badge = (
                "<span class='tag tag-green'>✅ متوازن</span>" if gap <= dec
                else "<span class='tag tag-orange'>⚠️ فجوة متوسطة</span>" if gap <= dec * 2
                else "<span class='tag tag-red'>❌ فجوة كبيرة</span>"
            )
            st.markdown(
                f"**{mat}**: معدل {target_m:.1f}h — أدنى {min_h}h — أعلى {max_hm}h — فرق {gap}h {badge}",
                unsafe_allow_html=True
            )

        st.markdown("---")
        rows_exp = []
        for mat in MATIERES:
            for p in get_profs(mat):
                dist  = st.session_state.distribution.get(p, {})
                for niv_id, h_val in dist.items():
                    if h_val <= 0:
                        continue
                    niv     = st.session_state.niveaux.get(niv_id, {})
                    h_unit  = niv.get("matieres", {}).get(mat, 0)
                    nb_cls  = (h_val // h_unit) if h_unit > 0 else 0
                    branche = niv.get("branche", "")
                    if nb_cls > 0:
                        rows_exp.append({
                            "المادة":              mat,
                            "رقم الأستاذ":         p.split("_")[-1],
                            "المستوى":             niv_id,
                            "تسمية المستوى":       niv.get("label", ""),
                            "الشعبة":              branche,
                            "عدد الأقسام":         nb_cls,
                            "الساعات/أسبوع":       h_val,
                            "الحمل الإجمالي (h)":  heures_prof_matiere(p, mat),
                        })
        if rows_exp:
            df_exp = pd.DataFrame(rows_exp)
            csv    = df_exp.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "📥 تصدير النتائج كاملة (CSV)",
                data=csv, file_name="توزيع_الأساتذة.csv",
                mime="text/csv", use_container_width=True,
            )