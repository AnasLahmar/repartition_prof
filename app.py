import streamlit as st
import pandas as pd
from copy import deepcopy
import math
from collections import defaultdict

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="توزيع الأساتذة",
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
MAX_HEURES    = 21
DECALAGE_MAX  = 3   # écart max autorisé entre profs de la même matière

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
    if "niveaux"        not in st.session_state: st.session_state.niveaux        = deepcopy(DEFAULT_NIVEAUX)
    if "niveaux_actifs" not in st.session_state: st.session_state.niveaux_actifs = list(DEFAULT_NIVEAUX.keys())
    if "nb_classes"     not in st.session_state: st.session_state.nb_classes     = {k:1 for k in DEFAULT_NIVEAUX}
    if "nb_profs"       not in st.session_state: st.session_state.nb_profs       = {m:1 for m in MATIERES}
    if "distribution"   not in st.session_state: st.session_state.distribution   = {}
    if "prof_config"    not in st.session_state: st.session_state.prof_config    = {}
    if "dist_log"       not in st.session_state: st.session_state.dist_log       = []
    if "dist_cls"       not in st.session_state: st.session_state.dist_cls       = {}
    if "decalage_max"   not in st.session_state: st.session_state.decalage_max   = DECALAGE_MAX

init_state()

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_profs(matiere):
    return [f"{matiere}_{i+1}" for i in range(st.session_state.nb_profs.get(matiere, 1))]

def all_profs():
    r = []
    for m in MATIERES: r.extend(get_profs(m))
    return r

def heures_prof(prof_id):
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




# ── Distribution algorithm ─────────────────────────────────────────────────────
def run_distribution():
    """
    RÈGLES FONDAMENTALES:
      1. Une classe = UN SEUL prof pour une matière donnée (jamais partagée)
      2. Chaque prof doit recevoir au moins 1 classe (≥ 1 h)
      3. Objectif : chaque prof se rapproche le plus possible de la MOYENNE
         moyenne = total_heures / nb_profs
         Comme on travaille en classes entières, certains profs auront floor(moy)
         et d'autres floor(moy) + h_unit (la différence ne dépasse jamais dec_max)
      4. Aucun prof ne dépasse max_h
      5. Gap entre profs de même matière ≤ dec_max

    STRATÉGIE:
      - On calcule la cible par prof = total / n_profs
      - On trie les classes par h DESC pour répartir les gros blocs en premier
      - On assigne chaque classe au prof le plus éloigné EN DESSOUS de sa cible
      - Après l'assignation : rebalancement itératif pour minimiser le gap
    """
    dist_cls = {}  # dist_cls[prof_id][niv_id] = nb_classes_entières (int)
    log      = []
    dec_max  = st.session_state.decalage_max
    max_h    = st.session_state.get("max_heures_cfg", MAX_HEURES)

    def hpc(niv_id, mat):
        """Heures par classe pour un niveau et une matière."""
        return st.session_state.niveaux[niv_id]["matieres"].get(mat, 0)

    def ph(p, mat):
        """Heures totales actuelles d'un prof pour une matière."""
        return sum(dist_cls.get(p, {}).get(n, 0) * hpc(n, mat)
                   for n in dist_cls.get(p, {}))

    def eligible(p, niv_id, mat):
        """Le prof est-il autorisé à enseigner ce niveau?"""
        elig = get_eligible_niveaux(p, mat)
        return (not elig) or (niv_id in elig)

    for mat in MATIERES:
        profs = get_profs(mat)
        if not profs:
            continue

        # Construction de la liste des tâches : une entrée PAR CLASSE
        # Une classe ne peut être attribuée qu'à UN SEUL prof
        tasks = []
        for niv_id in st.session_state.niveaux_actifs:
            h  = hpc(niv_id, mat)
            nb = st.session_state.nb_classes.get(niv_id, 1)
            if h > 0 and nb > 0:
                for cls_idx in range(nb):
                    tasks.append((niv_id, h, cls_idx))  # (niveau, h/classe, index_classe)

        if not tasks:
            continue

        total_h  = sum(h for _, h, _ in tasks)
        n_profs  = len(profs)
        target   = total_h / n_profs  # cible idéale par prof

        for p in profs:
            dist_cls.setdefault(p, {})

        # ── ÉTAPE 1 : Assignation en respectant la cible ───────────────────
        # Trier par h DESC : les grandes classes en premier pour mieux équilibrer
        for niv_id, h, _ in sorted(tasks, key=lambda x: -x[1]):
            # Profs éligibles pour ce niveau
            pool = [p for p in profs if eligible(p, niv_id, mat)]
            if not pool:
                pool = profs  # fallback : ignorer les restrictions

            # Parmi le pool, préférer ceux sous le plafond
            under_cap = [p for p in pool if ph(p, mat) + h <= max_h]
            active = under_cap if under_cap else pool

            # Choisir le prof le plus loin EN DESSOUS de la cible
            # (= celui dont ph(p) - target est le plus petit / le plus négatif)
            chosen = min(active, key=lambda p: ph(p, mat) - target)
            dist_cls[chosen][niv_id] = dist_cls[chosen].get(niv_id, 0) + 1

            if ph(chosen, mat) > max_h:
                log.append(f"⚠️ {mat}: أستاذ {chosen.split('_')[-1]} تجاوز {max_h}h (لا يوجد حل أفضل)")

        # ── ÉTAPE 2 : Garantir qu'aucun prof n'a 0 heure ─────────────────
        for _it in range(n_profs * (len(tasks) + 5)):
            zeros = [p for p in profs if ph(p, mat) == 0]
            if not zeros:
                break
            zp = zeros[0]

            # Donateurs : du plus chargé au moins chargé
            donors = sorted(
                [p for p in profs if p != zp and ph(p, mat) > 0],
                key=lambda p: ph(p, mat), reverse=True
            )
            done = False
            for donor in donors:
                # Tester chaque classe détenue par le donateur (plus petite h en premier)
                donor_niveaux = sorted(
                    [(n, hpc(n, mat))
                     for n, c in dist_cls.get(donor, {}).items()
                     if c > 0 and hpc(n, mat) > 0],
                    key=lambda x: x[1]
                )
                for niv_id, h in donor_niveaux:
                    if not eligible(zp, niv_id, mat):
                        continue
                    if ph(zp, mat) + h > max_h:
                        continue
                    # Transfert d'une classe entière
                    dist_cls[donor][niv_id] -= 1
                    if dist_cls[donor][niv_id] == 0:
                        del dist_cls[donor][niv_id]
                    dist_cls[zp][niv_id] = dist_cls[zp].get(niv_id, 0) + 1
                    log.append(
                        f"🔄 {mat}: نقل قسم {niv_id}({h}h) "
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

        # ── ÉTAPE 3 : Rééquilibrage pour respecter dec_max ────────────────
        # Répéter jusqu'à stabilisation ou épuisement des itérations
        for _it in range(500):
            h_vals  = [ph(p, mat) for p in profs]
            cur_gap = max(h_vals) - min(h_vals)
            if cur_gap <= dec_max:
                break

            max_p = max(profs, key=lambda p: ph(p, mat))
            min_p = min(
                [p for p in profs if ph(p, mat) > 0],
                key=lambda p: ph(p, mat),
                default=None
            )
            if min_p is None or max_p == min_p:
                break

            # Chercher la plus petite unité transférable qui améliore le gap
            candidates = sorted(
                [(n, hpc(n, mat))
                 for n, c in dist_cls.get(max_p, {}).items()
                 if c > 0 and hpc(n, mat) > 0],
                key=lambda x: x[1]  # plus petite h en premier
            )
            moved = False
            for niv_id, h in candidates:
                if not eligible(min_p, niv_id, mat):
                    continue
                if ph(min_p, mat) + h > max_h:
                    continue
                new_gap = abs((ph(max_p, mat) - h) - (ph(min_p, mat) + h))
                if new_gap >= cur_gap:
                    continue  # pas d'amélioration
                dist_cls[max_p][niv_id] -= 1
                if dist_cls[max_p][niv_id] == 0:
                    del dist_cls[max_p][niv_id]
                dist_cls[min_p][niv_id] = dist_cls[min_p].get(niv_id, 0) + 1
                moved = True
                break
            if not moved:
                break  # plus d'amélioration possible

        # Rapport final du gap pour cette matière
        h_vals    = [ph(p, mat) for p in profs]
        final_gap = max(h_vals) - min(h_vals)
        if final_gap > dec_max:
            log.append(
                f"⚠️ {mat}: الفجوة النهائية {final_gap}h > {dec_max}h — "
                f"قيود الشعب/المستويات تمنع التوازن الكامل"
            )

    # ── Conversion dist_cls → dist_hours pour le stockage ────────────────────
    dist_hours = {}
    for mat in MATIERES:
        for p in get_profs(mat):
            dist_hours.setdefault(p, {})
            for niv_id, nb_cls in dist_cls.get(p, {}).items():
                h = hpc(niv_id, mat)
                if nb_cls > 0 and h > 0:
                    dist_hours[p][niv_id] = dist_hours[p].get(niv_id, 0) + nb_cls * h

    # ── Vérification d'intégrité : somme = total requis ──────────────────────
    for mat in MATIERES:
        needed   = total_heures_needed(mat)
        assigned = sum(sum(dist_hours.get(p, {}).values()) for p in get_profs(mat))
        if needed > 0 and assigned != needed:
            log.append(f"⚠️ {mat}: موزع {assigned}h ≠ مطلوب {needed}h")

    st.session_state.distribution = dist_hours
    st.session_state.dist_cls     = dist_cls
    st.session_state.dist_log     = log
    return log



init_state()

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_profs(matiere):
    return [f"{matiere}_{i+1}" for i in range(st.session_state.nb_profs.get(matiere, 1))]

def all_profs():
    r = []
    for m in MATIERES: r.extend(get_profs(m))
    return r

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


# ── Distribution algorithm ─────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🏫 إدارة الأساتذة")
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
            avg_h = sum(nonzero)/len(nonzero)
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
                    if niv["branche"] != branche: continue
                    checked = niv_id in st.session_state.niveaux_actifs
                    new_val = st.checkbox(f"{niv_id} — {niv['label']}", value=checked, key=f"actif_{niv_id}")
                    if new_val and niv_id not in st.session_state.niveaux_actifs:
                        st.session_state.niveaux_actifs.append(niv_id)
                    elif not new_val and niv_id in st.session_state.niveaux_actifs:
                        st.session_state.niveaux_actifs.remove(niv_id)

    with tab2:
        st.markdown("<div class='section-header'>عدد الأقسام لكل مستوى</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i, branche in enumerate(BRANCHES):
            with cols[i]:
                st.markdown(f"**{branche}**")
                for niv_id in [k for k,v in st.session_state.niveaux.items()
                               if v["branche"]==branche and k in st.session_state.niveaux_actifs]:
                    niv = st.session_state.niveaux[niv_id]
                    val = st.number_input(niv["label"], min_value=0, max_value=20,
                                          value=st.session_state.nb_classes.get(niv_id,1),
                                          key=f"cls_{niv_id}")
                    st.session_state.nb_classes[niv_id] = val

    with tab3:
        st.markdown("<div class='section-header'>ساعات كل مادة بكل مستوى (قابلة للتعديل)</div>", unsafe_allow_html=True)
        actifs = st.session_state.niveaux_actifs
        if not actifs:
            st.warning("لا توجد مستويات نشطة")
        else:
            for niv_id in actifs:
                niv = st.session_state.niveaux[niv_id]
                with st.expander(f"📝 {niv_id} — {niv['label']}"):
                    c1,c2,c3 = st.columns(3)
                    for j, mat in enumerate(MATIERES):
                        with [c1,c2,c3][j%3]:
                            val = st.number_input(mat, min_value=0, max_value=30,
                                                   value=niv["matieres"].get(mat,0),
                                                   key=f"h_{niv_id}_{mat}")
                            st.session_state.niveaux[niv_id]["matieres"][mat] = val
            st.markdown("---")
            st.markdown("**ملخص الساعات:**")
            disp = {st.session_state.niveaux[n]["label"]:
                    {m: st.session_state.niveaux[n]["matieres"].get(m,0) for m in MATIERES}
                    for n in actifs}
            st.dataframe(pd.DataFrame(disp, index=MATIERES), use_container_width=True)


    with tab4:
        st.markdown("<div class='section-header'>⚖️ معاملات التوزيع التلقائي</div>", unsafe_allow_html=True)
        st.caption("هذه الإعدادات تتحكم في خوارزمية توزيع الحصص بين الأساتذة")
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            st.markdown("##### الحد الأقصى للساعات الأسبوعية / أستاذ")
            new_max = st.number_input(
                "الحد الأقصى (ساعة/أسبوع)",
                min_value=10, max_value=35,
                value=st.session_state.get("max_heures_cfg", MAX_HEURES),
                key="max_heures_cfg",
                help="لا يمكن لأي أستاذ تجاوز هذا العدد من الساعات في الأسبوع"
            )
        with col_cfg2:
            st.markdown("##### الفارق الأقصى المسموح بين أساتذة نفس المادة")
            new_dec = st.number_input(
                "الفارق الأقصى (ساعة)",
                min_value=0, max_value=10,
                value=st.session_state.decalage_max,
                key="decalage_max",
                help="مثال: 3 يعني لا يمكن أن يكون الفرق أكثر من 3 ساعات بين أساتذة نفس المادة"
            )
            color = "#16a34a" if new_dec <= 3 else "#d97706" if new_dec <= 6 else "#dc2626"
            label = "توازن ممتاز" if new_dec <= 3 else "مقبول" if new_dec <= 6 else "فجوة كبيرة"
            st.info(f"الفارق المسموح: **{new_dec}h** — {label}")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='value'>{st.session_state.get('max_heures_cfg', MAX_HEURES)}h</div><div class='label'>الحد الأقصى/أستاذ</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><div class='value'>{st.session_state.decalage_max}h</div><div class='label'>الفارق الأقصى المسموح</div></div>", unsafe_allow_html=True)
        with c3:
            total_needed = sum(total_heures_needed(m) for m in MATIERES)
            st.markdown(f"<div class='metric-card'><div class='value'>{total_needed}h</div><div class='label'>إجمالي الساعات المطلوبة</div></div>", unsafe_allow_html=True)


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
            with cols[i%3]:
                needed    = total_heures_needed(mat)
                suggested = max(1, math.ceil(needed / MAX_HEURES))
                val = st.number_input(
                    mat, min_value=1, max_value=20,
                    value=st.session_state.nb_profs.get(mat,1),
                    key=f"np_{mat}",
                    help=f"الساعات المطلوبة: {needed}h | مقترح: {suggested} أستاذ"
                )
                st.session_state.nb_profs[mat] = val
                if needed > 0:
                    avg   = needed / val
                    floor = int(needed // val)
                    extra = needed - floor * val
                    icon  = "🔴" if avg > MAX_HEURES else "🟢" if avg >= 15 else "🟡"
                    # Pre-compute to avoid f-string conditional bug
                    if extra:
                        ideal_str = f"{floor}h × {val-int(extra)} + {floor+1}h × {int(extra)}"
                    else:
                        ideal_str = f"{floor}h × {val}"
                    st.caption(f"{icon} {needed}h ÷ {val} = **{avg:.1f}h/أستاذ** | مثالي: {ideal_str}")


    with tab2:
        st.markdown("<div class='section-header'>تخصيص كل أستاذ — الشعب المسموحة والمستويات</div>", unsafe_allow_html=True)
        st.info("📌 كل أستاذ يمكن ربطه بـ **شعبتين كحد أقصى**. يمكنك تحديد مستويات بعينها أو تركها فارغة للسماح بكل المستويات.")

        sel_mat = st.selectbox("اختر المادة لتخصيص أساتذتها", MATIERES, key="sel_mat_cfg")
        profs   = get_profs(sel_mat)

        # Info box: total hours + target for this matière
        needed_sel   = total_heures_needed(sel_mat)
        nb_profs_sel = len(profs)
        target_sel   = needed_sel / nb_profs_sel if nb_profs_sel else 0
        floor_sel    = int(needed_sel // nb_profs_sel) if nb_profs_sel else 0
        extra_sel    = needed_sel - floor_sel * nb_profs_sel if nb_profs_sel else 0
        dec_disp     = st.session_state.decalage_max
        # Pre-compute distribution string to avoid f-string conditional rendering bug
        if extra_sel:
            dist_ideal_str = f"{floor_sel}h × {nb_profs_sel - int(extra_sel)} + {floor_sel+1}h × {int(extra_sel)} أستاذ"
        else:
            dist_ideal_str = f"{floor_sel}h × {nb_profs_sel} أستاذ"

        col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
        col_i1.metric("إجمالي ساعات " + sel_mat, f"{needed_sel}h")
        col_i2.metric("عدد الأساتذة", str(nb_profs_sel))
        col_i3.metric("المعدل المستهدف", f"{target_sel:.1f}h")
        col_i4.metric("التوزيع المثالي", dist_ideal_str)
        col_i5.metric("الفارق الأقصى المسموح", f"{dec_disp}h")
        st.divider()


        for prof_id in profs:
            cfg = st.session_state.prof_config.get(prof_id, {})
            # Hours for this prof in THIS matière only
            dist_p = st.session_state.distribution.get(prof_id, {})
            h_mat  = sum(
                v for n, v in dist_p.items()
                if n in st.session_state.niveaux_actifs
                and st.session_state.niveaux[n]["matieres"].get(sel_mat, 0) > 0
            ) if st.session_state.distribution else 0
            diff_t   = h_mat - target_sel
            lbl_diff = f"  {diff_t:+.0f}h vs معدل" if st.session_state.distribution else ""
            hcolor   = "🟢" if abs(diff_t) <= dec_disp else "🔴"
            with st.expander(f"👤 أستاذ {prof_id.split('_')[-1]}  —  {sel_mat}  |  {h_mat}h{lbl_diff}  {hcolor if st.session_state.distribution else ''}"):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**الشعب المسموحة (2 كحد أقصى)**")
                    widget_key_br = f"br_{prof_id}"
                    if widget_key_br in st.session_state:
                        stored = st.session_state[widget_key_br]
                        if isinstance(stored, list) and len(stored) > 2:
                            st.session_state[widget_key_br] = stored[:2]
                    current_branches = cfg.get("branches", [])
                    default_br = [b for b in current_branches if b in BRANCHES][:2]
                    sel_branches = st.multiselect(
                        "الشعب", BRANCHES,
                        default=default_br,
                        key=widget_key_br, max_selections=2,
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
                n_html = "".join([f"<span class='tag tag-green'>{n}</span>" for n in sel_niveaux]) if sel_niveaux                          else "<span class='tag tag-gray'>جميع المستويات</span>"
                st.markdown(f"**الشعب:** {b_html} &nbsp;&nbsp; **المستويات:** {n_html}", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — LANCER LA RÉPARTITION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚀 تشغيل التوزيع":
    st.markdown("# 🚀 تشغيل التوزيع")

    # Pre-flight warnings
    warnings_pre = []
    for mat in MATIERES:
        needed = total_heures_needed(mat)
        nb     = st.session_state.nb_profs.get(mat, 1)
        if needed > 0 and nb * MAX_HEURES < needed:
            warnings_pre.append(f"**{mat}**: {needed}h مطلوبة — {nb} أستاذ × {MAX_HEURES}h = {nb*MAX_HEURES}h فقط")

    if warnings_pre:
        st.warning("⚠️ **تنبيه:** عدد الأساتذة قد لا يكفي لهذه المواد:")
        for w in warnings_pre:
            st.markdown(f"- {w}")
        st.markdown("---")

    # Summary table
    st.markdown("<div class='section-header'>ملخص ما سيتم توزيعه</div>", unsafe_allow_html=True)
    rows_prev = []
    for mat in MATIERES:
        needed = total_heures_needed(mat)
        if needed == 0: continue
        nb  = st.session_state.nb_profs.get(mat, 1)
        avg = needed / nb if nb else 0
        rows_prev.append({
            "المادة":          mat,
            "إجمالي الساعات":  needed,
            "عدد الأساتذة":    nb,
            "المعدل المتوقع":  f"{avg:.1f}h",
            "الحالة":          "✅ مناسب" if avg <= MAX_HEURES else "🔴 تجاوز"
        })
    if rows_prev:
        st.dataframe(pd.DataFrame(rows_prev), use_container_width=True, hide_index=True)

    st.markdown("---")

    # LAUNCH BOX
    st.markdown("""
    <div class='launch-box'>
        <div class='launch-title'>🎯 جاهز لتشغيل التوزيع التلقائي</div>
        <div class='launch-sub'>
            سيتم توزيع الحصص بشكل متوازن بين الأساتذة<br>
            مع احترام الحد الأقصى 21 ساعة/أسبوع وتخصيصات كل أستاذ
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,2,1])
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

    # Manual override (only if distribution exists)
    if st.session_state.distribution:
        st.markdown("<div class='section-header'>✏️ تعديل يدوي بعد التوزيع</div>", unsafe_allow_html=True)
        st.caption("يمكنك تعديل قيم التوزيع يدوياً لكل أستاذ ومستوى")

        sel_mat_m = st.selectbox("اختر المادة للتعديل", MATIERES, key="man_mat")
        profs_m   = get_profs(sel_mat_m)
        niv_mat   = [k for k in st.session_state.niveaux_actifs
                     if st.session_state.niveaux[k]["matieres"].get(sel_mat_m, 0) > 0]

        if not niv_mat:
            st.info("لا توجد مستويات لهذه المادة")
        else:
            needed_m = total_heures_needed(sel_mat_m)
            nb_m     = len(profs_m)
            target_m = needed_m / nb_m if nb_m else 0
            max_h_cfg = st.session_state.get("max_heures_cfg", MAX_HEURES)

            for prof_id in profs_m:
                dist = st.session_state.distribution.setdefault(prof_id, {})
                # Hours for this prof in THIS matière only
                h_mat = sum(
                    v for n, v in dist.items()
                    if n in st.session_state.niveaux_actifs
                    and st.session_state.niveaux[n]["matieres"].get(sel_mat_m, 0) > 0
                )
                diff_t = h_mat - target_m
                icon   = "🟢" if abs(diff_t) <= st.session_state.decalage_max else "🔴"
                with st.expander(
                    f"👤 أستاذ {prof_id.split('_')[-1]} — {sel_mat_m} "
                    f"| {h_mat}h ({diff_t:+.0f}h vs معدل {target_m:.1f}h) {icon}"
                ):
                    sub_cols = st.columns(4)
                    for j, niv_id in enumerate(niv_mat):
                        niv   = st.session_state.niveaux[niv_id]
                        h_max = niv["matieres"].get(sel_mat_m, 0) * st.session_state.nb_classes.get(niv_id, 1)
                        cur   = int(dist.get(niv_id, 0))
                        with sub_cols[j%4]:
                            val = st.number_input(
                                niv["label"], min_value=0, max_value=int(h_max),
                                value=cur, key=f"man_{prof_id}_{niv_id}",
                                help=f"Max: {h_max}h ({int(h_max // niv['matieres'].get(sel_mat_m,1))} قسم)"
                            )
                            st.session_state.distribution[prof_id][niv_id] = val

                    # Recalculate after edit
                    h_mat_new = sum(
                        v for n, v in dist.items()
                        if n in st.session_state.niveaux_actifs
                        and st.session_state.niveaux[n]["matieres"].get(sel_mat_m, 0) > 0
                    )
                    pct = min(h_mat_new / max_h_cfg * 100, 100)
                    fc  = "#16a34a" if h_mat_new <= max_h_cfg else "#dc2626"
                    st.markdown(
                        f"<div style='margin-top:8px'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px'>"
                        f"<span style='color:#64748b;font-size:0.85rem'>ساعات {sel_mat_m} لهذا الأستاذ</span>"
                        f"<span style='color:{fc};font-weight:700'>{h_mat_new}h / {max_h_cfg}h</span>"
                        f"</div>"
                        f"<div style='height:10px;background:#e2e8f0;border-radius:5px;overflow:hidden'>"
                        f"<div style='width:{pct}%;height:100%;background:{fc};border-radius:5px'></div>"
                        f"</div></div>",
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
        st.markdown("<div class='section-header'>حصص كل أستاذ</div>", unsafe_allow_html=True)
        filter_mat = st.selectbox("تصفية حسب المادة", ["الكل"] + MATIERES, key="flt_res")
        mats_show  = MATIERES if filter_mat == "الكل" else [filter_mat]
        for mat in mats_show:
            needed  = total_heures_needed(mat)
            n_profs = st.session_state.nb_profs.get(mat, 1)
            target  = needed / n_profs if n_profs else 0
            rows = []
            for p in get_profs(mat):
                h    = heures_prof(p)
                dist = st.session_state.distribution.get(p, {})
                niv_list = [f"{st.session_state.niveaux[n]['label']}({v}h)"
                            for n,v in dist.items() if v>0 and n in st.session_state.niveaux_actifs]
                diff_target = h - target
                rows.append({
                    "الأستاذ":              f"أستاذ {p.split('_')[-1]}",
                    "إجمالي الساعات":       h,
                    "الهدف (المعدل)":       f"{target:.1f}h",
                    "الفرق عن المعدل":      f"{diff_target:+.1f}h",
                    "المستويات المُسندة":   " | ".join(niv_list) or "—",
                    "الحالة": ("🔴 تجاوز الحد" if h > MAX_HEURES
                                else "❌ لم يُسند" if h == 0
                                else "✅ جيد"),
                })
            if rows:
                # Add total row
                total_assigned = sum(r["إجمالي الساعات"] for r in rows)
                rows.append({
                    "الأستاذ":             "📊 المجموع",
                    "إجمالي الساعات":      total_assigned,
                    "الهدف (المعدل)":      f"المطلوب: {needed}h",
                    "الفرق عن المعدل":     ("✅ = " if total_assigned==needed else f"❌ فارق {total_assigned-needed:+d}h"),
                    "المستويات المُسندة":  "",
                    "الحالة":              ("✅ مطابق" if total_assigned==needed else "❌ خطأ"),
                })
                st.markdown(f"#### 📖 {mat}  —  المطلوب: **{needed}h**  |  المعدل المستهدف: **{target:.1f}h/أستاذ**")
                df_show = pd.DataFrame(rows)
                st.dataframe(df_show, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("<div class='section-header'>مقارنة الساعات المطلوبة والموزعة</div>", unsafe_allow_html=True)
        st.info("✅ **قاعدة التحقق:** مجموع ساعات أساتذة كل مادة يجب أن يساوي تماماً إجمالي ساعات تلك المادة")

        rows = []
        total_needed_all  = 0
        total_assigned_all = 0
        all_balanced = True

        for mat in MATIERES:
            needed   = total_heures_needed(mat)
            assigned = sum(sum(st.session_state.distribution.get(p,{}).values()) for p in get_profs(mat))
            diff     = assigned - needed
            total_needed_all   += needed
            total_assigned_all += assigned
            if diff != 0:
                all_balanced = False
            rows.append({
                "المادة":           mat,
                "الساعات المطلوبة": needed,
                "الساعات الموزعة":  assigned,
                "الفرق":            diff,
                "عدد الأساتذة":     st.session_state.nb_profs.get(mat,1),
                "الحالة": ("✅ متوازن" if diff==0
                            else f"➕ زيادة {diff}h" if diff>0
                            else f"➖ نقص {abs(diff)}h"),
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        # Grand total verification box
        diff_total = total_assigned_all - total_needed_all
        box_color  = "#f0fdf4" if diff_total == 0 else "#fef2f2"
        brd_color  = "#86efac" if diff_total == 0 else "#fca5a5"
        icon       = "✅" if diff_total == 0 else "❌"
        msg        = "التوزيع مكتمل — كل الساعات موزعة بشكل صحيح" if diff_total == 0 else f"تحذير: فارق {abs(diff_total)}h بين الساعات المطلوبة والموزعة"
        st.markdown(f"""
        <div style="background:{box_color};border:2px solid {brd_color};border-radius:12px;padding:16px 20px;margin-top:8px">
            <div style="font-size:1.1rem;font-weight:800;color:#1e293b;margin-bottom:8px">{icon} التحقق الإجمالي</div>
            <div style="display:flex;gap:32px;flex-wrap:wrap">
                <div><span style="color:#64748b;font-size:0.85rem">إجمالي الساعات المطلوبة</span><br>
                     <span style="font-size:1.4rem;font-weight:900;color:#0284c7">{total_needed_all}h</span></div>
                <div><span style="color:#64748b;font-size:0.85rem">إجمالي الساعات الموزعة</span><br>
                     <span style="font-size:1.4rem;font-weight:900;color:#16a34a">{total_assigned_all}h</span></div>
                <div><span style="color:#64748b;font-size:0.85rem">الفارق</span><br>
                     <span style="font-size:1.4rem;font-weight:900;color:{'#16a34a' if diff_total==0 else '#dc2626'}">{diff_total:+d}h</span></div>
            </div>
            <div style="margin-top:10px;color:#475569;font-size:0.9rem">{msg}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        # KPIs
        all_h   = [heures_prof(p) for p in all_profs()]
        nonzero = [h for h in all_h if h > 0]
        avg_kpi = sum(nonzero)/len(nonzero) if nonzero else 0
        over_kpi = sum(1 for h in all_h if h > MAX_HEURES)
        low_kpi  = sum(1 for h in all_h if 0 < h < 12)

        c1,c2,c3,c4 = st.columns(4)
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
        st.markdown("### 📊 الحمل الأسبوعي لكل أستاذ")
        for mat in MATIERES:
            profs_m  = get_profs(mat)
            if not any(heures_prof(p) > 0 for p in profs_m): continue
            st.markdown(f"**{mat}**")
            for p in profs_m:
                h   = heures_prof(p)
                pct = min(h/MAX_HEURES*100, 100)
                col = "#16a34a" if h<=MAX_HEURES else "#dc2626"
                lbl = p.split("_")[-1]
                st.markdown(f"""
                <div class='result-row'>
                    <span style="min-width:70px;color:#475569;font-size:0.85rem">أستاذ {lbl}</span>
                    <div style="flex:1;height:12px;background:#e2e8f0;border-radius:6px;overflow:hidden">
                        <div style="width:{pct}%;height:100%;background:{col};border-radius:6px"></div>
                    </div>
                    <span style="min-width:55px;text-align:right;color:{col};font-weight:700;font-size:0.9rem">{h}h</span>
                    <span style="color:#94a3b8;font-size:0.75rem">/ {MAX_HEURES}h</span>
                </div>""", unsafe_allow_html=True)

        # Equity analysis
        st.markdown("---")
        st.markdown("### ⚖️ تحليل التوازن بين الأساتذة")
        for mat in MATIERES:
            profs_m  = get_profs(mat)
            hours_m  = [heures_prof(p) for p in profs_m]
            if not any(h>0 for h in hours_m): continue
            min_h, max_h = min(hours_m), max(hours_m)
            gap = max_h - min_h
            dec   = st.session_state.decalage_max
            badge = ("<span class='tag tag-green'>✅ متوازن</span>" if gap<=dec
                     else "<span class='tag tag-orange'>⚠️ فجوة متوسطة</span>" if gap<=dec*2
                     else "<span class='tag tag-red'>❌ فجوة كبيرة</span>")
            st.markdown(f"**{mat}**: أدنى {min_h}h — أعلى {max_h}h — فرق {gap}h {badge}",
                        unsafe_allow_html=True)

        # Export
        st.markdown("---")
        rows_exp = []
        for mat in MATIERES:
            for p in get_profs(mat):
                for niv_id, h in st.session_state.distribution.get(p, {}).items():
                    if h > 0:
                        niv = st.session_state.niveaux.get(niv_id, {})
                        rows_exp.append({
                            "المادة":          mat,
                            "رقم الأستاذ":     p.split("_")[-1],
                            "المستوى":         niv_id,
                            "تسمية المستوى":   niv.get("label",""),
                            "الساعات/أسبوع":   h,
                            "الحمل الإجمالي":  heures_prof(p),
                        })
        if rows_exp:
            df_exp = pd.DataFrame(rows_exp)
            csv    = df_exp.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "📥 تصدير النتائج كاملة (CSV)",
                data=csv, file_name="توزيع_الأساتذة.csv",
                mime="text/csv", use_container_width=True,
            )