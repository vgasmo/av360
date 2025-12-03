import streamlit as st
import sqlite3
import hashlib
from datetime import date
import pandas as pd

DB_PATH = "avaliacao360.db"

# ---------- BASE DE DADOS ----------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_db():
    conn = get_conn()
    cur = conn.cursor()

    # Tabelas base
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_teams (
            user_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            is_primary INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, team_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(team_id) REFERENCES teams(id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS competencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            team_id INTEGER,
            leadership_only INTEGER NOT NULL DEFAULT 0,
            weight REAL NOT NULL DEFAULT 1.0,
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(team_id) REFERENCES teams(id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_id INTEGER NOT NULL,
            evaluator_id INTEGER NOT NULL,
            evaluatee_id INTEGER NOT NULL,
            include_behavioral INTEGER NOT NULL DEFAULT 0,
            include_technical INTEGER NOT NULL DEFAULT 0,
            include_objectives INTEGER NOT NULL DEFAULT 0,
            UNIQUE(period_id, evaluator_id, evaluatee_id),
            FOREIGN KEY(period_id) REFERENCES evaluation_periods(id),
            FOREIGN KEY(evaluator_id) REFERENCES users(id),
            FOREIGN KEY(evaluatee_id) REFERENCES users(id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            competency_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            comment TEXT,
            UNIQUE(assignment_id, competency_id),
            FOREIGN KEY(assignment_id) REFERENCES evaluation_assignments(id),
            FOREIGN KEY(competency_id) REFERENCES competencies(id)
        );
    """)

    conn.commit()

    # Equipas
    teams = [
        ("Marketing",),
        ("Administrativo",),
        ("Projetos",),
        ("Consultoria & Ecossistema",),
    ]
    cur.executemany("INSERT OR IGNORE INTO teams(name) VALUES (?)", teams)

    # Utilizadores
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        def h(p: str) -> str:
            return hashlib.sha256(p.encode("utf-8")).hexdigest()

        base_users = [
            ("Vítor", "vitor@empresa.local", "1234", "CEO"),
            ("Francisco", "francisco@empresa.local", "1234", "RESPONSAVEL"),
            ("Natacha", "natacha@empresa.local", "1234", "MEMBRO"),
            ("Mariana", "mariana@empresa.local", "1234", "MEMBRO"),
            ("Nicole", "nicole@empresa.local", "1234", "ESTAGIARIO"),
            ("Ana", "ana@empresa.local", "1234", "RESPONSAVEL"),
            ("Paula", "paula@empresa.local", "1234", "MEMBRO"),
            ("Bruno", "bruno@empresa.local", "1234", "RESPONSAVEL"),
            ("Rita", "rita@empresa.local", "1234", "MEMBRO"),
            ("Bernardo", "bernardo@empresa.local", "1234", "ESTAGIARIO"),
            ("Luís Fonseca", "luis@empresa.local", "1234", "MEMBRO"),
            ("Margarida", "margarida@empresa.local", "1234", "MEMBRO"),
            ("Pacheco", "pacheco@empresa.local", "1234", "ESTAGIARIO"),
            ("João", "joao@empresa.local", "1234", "RESPONSAVEL"),
            ("Colaço", "colaco@empresa.local", "1234", "MEMBRO"),
            ("Sandra", "sandra@empresa.local", "1234", "ESTAGIARIO"),
            ("Cláudia", "claudia@empresa.local", "1234", "ESTAGIARIO"),
        ]
        cur.executemany(
            "INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)",
            [(n, e, h(p), r) for (n, e, p, r) in base_users],
        )

    # Ligações utilizador–equipa
    cur.execute("SELECT COUNT(*) AS c FROM user_teams")
    if cur.fetchone()["c"] == 0:
        def user_id(email: str):
            cur.execute("SELECT id FROM users WHERE email=?", (email,))
            row = cur.fetchone()
            return row["id"] if row else None

        def team_id(name: str):
            cur.execute("SELECT id FROM teams WHERE name=?", (name,))
            row = cur.fetchone()
            return row["id"] if row else None

        links = []

        # Marketing
        for email in ["francisco@empresa.local", "natacha@empresa.local", "mariana@empresa.local", "nicole@empresa.local"]:
            links.append((user_id(email), team_id("Marketing"), 1 if email == "francisco@empresa.local" else 0))

        # Administrativo
        for email in ["ana@empresa.local", "paula@empresa.local", "bruno@empresa.local", "rita@empresa.local", "bernardo@empresa.local"]:
            links.append((user_id(email), team_id("Administrativo"), 1 if email == "ana@empresa.local" else 0))

        # Projetos
        for email in ["luis@empresa.local", "bruno@empresa.local", "margarida@empresa.local", "pacheco@empresa.local"]:
            links.append((user_id(email), team_id("Projetos"), 1 if email == "bruno@empresa.local" else 0))

        # Consultoria & Ecossistema
        for email in [
            "joao@empresa.local",
            "colaco@empresa.local",
            "francisco@empresa.local",
            "vitor@empresa.local",
            "bruno@empresa.local",
            "margarida@empresa.local",
            "luis@empresa.local",
            "sandra@empresa.local",
            "claudia@empresa.local",
        ]:
            links.append((user_id(email), team_id("Consultoria & Ecossistema"), 1 if email == "joao@empresa.local" else 0))

        links = [l for l in links if l[0] is not None and l[1] is not None]
        cur.executemany(
            "INSERT OR IGNORE INTO user_teams(user_id,team_id,is_primary) VALUES (?,?,?)",
            links,
        )

    # Competências
    cur.execute("SELECT COUNT(*) AS c FROM competencies")
    if cur.fetchone()["c"] == 0:
        behavioral = [
            ("Colaboração & Trabalho em Equipa",
             "Contribui de forma construtiva para o trabalho em equipa e apoia colegas quando necessário.",
             "BEHAVIORAL", None, 0, 1.0),
            ("Comunicação",
             "Comunica de forma clara, ajustando a mensagem ao interlocutor e ouvindo ativamente.",
             "BEHAVIORAL", None, 0, 1.0),
            ("Responsabilidade & Fiabilidade",
             "Cumpre prazos, assume responsabilidade pelos erros e é alguém em quem se pode confiar.",
             "BEHAVIORAL", None, 0, 1.0),
            ("Orientação para Resultados",
             "Mantém foco nos objetivos, prioriza bem e entrega trabalho com qualidade.",
             "BEHAVIORAL", None, 0, 1.0),
            ("Proatividade & Inovação",
             "Antecipar problemas, propõe melhorias e está disponível para experimentar novas abordagens.",
             "BEHAVIORAL", None, 0, 1.0),
            ("Desenvolvimento & Aprendizagem Contínua",
             "Procura feedback, atualiza conhecimentos e aprende com os erros.",
             "BEHAVIORAL", None, 0, 1.0),
            ("Liderança",
             "Dá orientação clara, apoia a equipa e reconhece o contributo dos outros.",
             "BEHAVIORAL", None, 1, 1.2),
        ]
        cur.executemany(
            "INSERT INTO competencies(name,description,category,team_id,leadership_only,weight) VALUES (?,?,?,?,?,?)",
            behavioral,
        )

        def t(name: str):
            cur.execute("SELECT id FROM teams WHERE name=?", (name,))
            r = cur.fetchone()
            return r["id"] if r else None

        marketing_comps = [
            ("Planeamento & Execução de Campanhas",
             "Planeia e executa campanhas alinhadas com os objetivos e prazos.",
             "TECHNICAL", t("Marketing")),
            ("Conteúdos & Copywriting",
             "Produz conteúdos claros, relevantes e ajustados ao público-alvo.",
             "TECHNICAL", t("Marketing")),
            ("Gestão de Redes Sociais & Comunidade",
             "Garante presença consistente e interação adequada com a comunidade.",
             "TECHNICAL", t("Marketing")),
            ("Análise de Métricas de Marketing",
             "Usa dados e métricas para melhorar campanhas e decisões.",
             "TECHNICAL", t("Marketing")),
            ("Branding & Posicionamento",
             "Respeita e reforça a identidade e posicionamento da marca.",
             "TECHNICAL", t("Marketing")),
        ]
        cur.executemany(
            "INSERT INTO competencies(name,description,category,team_id) VALUES (?,?,?,?)",
            marketing_comps,
        )

        admin_comps = [
            ("Organização & Gestão de Tarefas",
             "Mantém processos e documentação bem organizados.",
             "TECHNICAL", t("Administrativo")),
            ("Rigor & Atenção ao Detalhe",
             "Minimiza erros em registos, documentos e processos.",
             "TECHNICAL", t("Administrativo")),
            ("Cumprimento de Procedimentos",
             "Segue procedimentos definidos e garante conformidade.",
             "TECHNICAL", t("Administrativo")),
            ("Apoio à Equipa & Atendimento",
             "Responde de forma profissional a pedidos internos e externos.",
             "TECHNICAL", t("Administrativo")),
            ("Eficiência Operacional",
             "Procura simplificar processos e usar bem as ferramentas digitais.",
             "TECHNICAL", t("Administrativo")),
        ]
        cur.executemany(
            "INSERT INTO competencies(name,description,category,team_id) VALUES (?,?,?,?)",
            admin_comps,
        )

        proj_comps = [
            ("Planeamento de Projetos",
             "Define objetivos, fases, prazos e recursos de forma clara.",
             "TECHNICAL", t("Projetos")),
            ("Gestão de Stakeholders",
             "Comunica e alinha expectativas com clientes, parceiros e equipa.",
             "TECHNICAL", t("Projetos")),
            ("Execução & Qualidade das Entregas",
             "Entrega outputs com qualidade e de acordo com os standards acordados.",
             "TECHNICAL", t("Projetos")),
            ("Controlo de Prazos & Orçamento",
             "Monitoriza prazos e custos, reagindo a desvios.",
             "TECHNICAL", t("Projetos")),
            ("Resolução de Problemas",
             "Identifica riscos e propõe alternativas realistas.",
             "TECHNICAL", t("Projetos")),
        ]
        cur.executemany(
            "INSERT INTO competencies(name,description,category,team_id) VALUES (?,?,?,?)",
            proj_comps,
        )

        cons_comps = [
            ("Diagnóstico & Pensamento Crítico",
             "Analisa a situação de clientes e parceiros com base em dados.",
             "TECHNICAL", t("Consultoria & Ecossistema")),
            ("Desenho de Soluções & Propostas de Valor",
             "Cria propostas claras, realistas e alinhadas com a estratégia do cliente.",
             "TECHNICAL", t("Consultoria & Ecossistema")),
            ("Facilitação & Formação",
             "Conduz reuniões, workshops e sessões de forma estruturada.",
             "TECHNICAL", t("Consultoria & Ecossistema")),
            ("Relação com Clientes & Parceiros",
             "Constrói confiança e mantém follow-up adequado.",
             "TECHNICAL", t("Consultoria & Ecossistema")),
            ("Networking & Desenvolvimento de Ecossistema",
             "Identifica e ativa oportunidades no ecossistema.",
             "TECHNICAL", t("Consultoria & Ecossistema")),
        ]
        cur.executemany(
            "INSERT INTO competencies(name,description,category,team_id) VALUES (?,?,?,?)",
            cons_comps,
        )

        objective_comps = [
            ("Cumprimento de Objetivos",
             "Grau de cumprimento dos objetivos acordados para o período.",
             "OBJECTIVES", None),
            ("Alinhamento com Prioridades",
             "Foco nas prioridades estratégicas da organização.",
             "OBJECTIVES", None),
            ("Qualidade dos Resultados",
             "Impacto e qualidade dos resultados alcançados.",
             "OBJECTIVES", None),
        ]
        cur.executemany(
            "INSERT INTO competencies(name,description,category,team_id) VALUES (?,?,?,?)",
            objective_comps,
        )

    # Período ativo inicial
    cur.execute("SELECT id FROM evaluation_periods WHERE is_active=1 LIMIT 1")
    row = cur.fetchone()
    if not row:
        today = date.today()
        name = f"Avaliação {today.year}"
        cur.execute(
            "INSERT INTO evaluation_periods(name,start_date,end_date,is_active) VALUES (?,?,?,1)",
            (name, str(today), str(today)),
        )

    conn.commit()
    conn.close()

def list_periods():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ep.*,
               (SELECT COUNT(*) FROM evaluation_assignments ea WHERE ea.period_id = ep.id) AS n_assignments
        FROM evaluation_periods ep
        ORDER BY start_date DESC, id DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def create_period(name: str, start_date_str: str, end_date_str: str, make_active: bool = True):
    conn = get_conn()
    cur = conn.cursor()
    if make_active:
        cur.execute("UPDATE evaluation_periods SET is_active=0")
    cur.execute(
        "INSERT INTO evaluation_periods(name,start_date,end_date,is_active) VALUES (?,?,?,?)",
        (name, start_date_str, end_date_str, 1 if make_active else 0),
    )
    period_id = cur.lastrowid
    conn.commit()
    conn.close()
    return period_id

def set_active_period(period_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE evaluation_periods SET is_active=0")
    cur.execute("UPDATE evaluation_periods SET is_active=1 WHERE id=?", (period_id,))
    conn.commit()
    conn.close()

def get_current_period_id():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM evaluation_periods WHERE is_active=1 ORDER BY start_date DESC, id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else None

def get_user_by_email(email: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND is_active=1", (email,))
    row = cur.fetchone()
    conn.close()
    return row

def verify_password(password: str, password_hash: str) -> bool:
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == password_hash

def shared_teams(user_a_id: int, user_b_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id
        FROM teams t
        JOIN user_teams ua ON ua.team_id=t.id
        JOIN user_teams ub ON ub.team_id=t.id
        WHERE ua.user_id=? AND ub.user_id=?
        """,
        (user_a_id, user_b_id),
    )
    rows = cur.fetchall()
    conn.close()
    return [r["id"] for r in rows]

def generate_assignments_for_period(period_id: int):
    """Todos avaliam todos: CEO incluído como avaliador e como avaliado."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE is_active=1")
    users = [r["id"] for r in cur.fetchall()]

    for evaluator in users:
        for evaluatee in users:
            include_behavioral = 1  # todos avaliam todos
            shared = shared_teams(evaluator, evaluatee)
            include_technical = 1 if shared else 0
            include_objectives = 1 if shared else 0

            if not (include_behavioral or include_technical or include_objectives):
                continue

            cur.execute(
                """
                INSERT OR IGNORE INTO evaluation_assignments
                (period_id, evaluator_id, evaluatee_id, include_behavioral, include_technical, include_objectives)
                VALUES (?,?,?,?,?,?)
                """,
                (period_id, evaluator, evaluatee, include_behavioral, include_technical, include_objectives),
            )

    conn.commit()
    conn.close()

def get_assignments_for_evaluator(user_id: int, period_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ea.*, u.name AS evaluatee_name
        FROM evaluation_assignments ea
        JOIN users u ON u.id = ea.evaluatee_id
        WHERE ea.evaluator_id=? AND ea.period_id=?
        ORDER BY u.name
        """,
        (user_id, period_id),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_competencies_for_assignment(assignment):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT role FROM users WHERE id=?", (assignment["evaluatee_id"],))
    eve_role = cur.fetchone()["role"]

    cur.execute("SELECT team_id FROM user_teams WHERE user_id=?", (assignment["evaluator_id"],))
    eval_teams = [r["team_id"] for r in cur.fetchall()]
    cur.execute("SELECT team_id FROM user_teams WHERE user_id=?", (assignment["evaluatee_id"],))
    eve_teams = [r["team_id"] for r in cur.fetchall()]
    shared = [t for t in eval_teams if t in eve_teams]

    cur.execute("SELECT * FROM competencies WHERE active=1")
    all_comps = cur.fetchall()
    conn.close()

    comps = []
    for c in all_comps:
        cat = c["category"]
        if cat == "BEHAVIORAL":
            if assignment["include_behavioral"] != 1:
                continue
            if c["leadership_only"] == 1 and eve_role not in ("CEO", "RESPONSAVEL"):
                continue
            comps.append(c)
        elif cat == "OBJECTIVES":
            if assignment["include_objectives"] != 1:
                continue
            comps.append(c)
        elif cat == "TECHNICAL":
            if assignment["include_technical"] != 1:
                continue
            if c["team_id"] is None:
                continue
            if c["team_id"] not in shared:
                continue
            comps.append(c)

    return comps

def get_existing_answers(assignment_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM evaluation_answers WHERE assignment_id=?", (assignment_id,))
    rows = cur.fetchall()
    conn.close()
    return {r["competency_id"]: r for r in rows}

def save_answers(assignment_id: int, answers):
    conn = get_conn()
    cur = conn.cursor()
    for comp_id, (score, comment) in answers.items():
        cur.execute(
            """
            INSERT INTO evaluation_answers(assignment_id, competency_id, score, comment)
            VALUES (?,?,?,?)
            ON CONFLICT(assignment_id, competency_id)
            DO UPDATE SET score=excluded.score, comment=excluded.comment
            """,
            (assignment_id, comp_id, score, comment),
        )
    conn.commit()
    conn.close()

def get_my_scores(user_id: int, period_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.category, AVG(ea.score) AS avg_score
        FROM evaluation_answers ea
        JOIN evaluation_assignments a ON a.id = ea.assignment_id
        JOIN competencies c ON c.id = ea.competency_id
        WHERE a.evaluatee_id=? AND a.period_id=?
        GROUP BY c.category
        """,
        (user_id, period_id),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_my_scores_over_time(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ep.name AS period_name,
               ep.start_date,
               c.category,
               AVG(ea.score) AS avg_score
        FROM evaluation_answers ea
        JOIN evaluation_assignments a ON a.id = ea.assignment_id
        JOIN competencies c ON c.id = ea.competency_id
        JOIN evaluation_periods ep ON ep.id = a.period_id
        WHERE a.evaluatee_id=?
        GROUP BY ep.id, ep.name, ep.start_date, c.category
        ORDER BY ep.start_date, ep.id, c.category
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_global_scores(period_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT u.name AS evaluatee_name,
               c.category,
               AVG(ea.score) AS avg_score
        FROM evaluation_answers ea
        JOIN evaluation_assignments a ON a.id = ea.assignment_id
        JOIN competencies c ON c.id = ea.competency_id
        JOIN users u ON u.id = a.evaluatee_id
        WHERE a.period_id=?
        GROUP BY u.name, c.category
        ORDER BY u.name, c.category
        """,
        (period_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def count_completed_assignments(assignments):
    done = 0
    total = len(assignments)
    for a in assignments:
        comps = get_competencies_for_assignment(a)
        existing = get_existing_answers(a["id"])
        if comps and len(existing) == len(comps):
            done += 1
    return done, total

# ---------- UI ----------

def inject_css():
    st.markdown(
        """
        <style>
        .main {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4edf7 100%);
        }
        .stMetric {
            background-color: white;
            padding: 0.75rem 1rem;
            border-radius: 0.75rem;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
        }
        .card {
            background-color: white;
            padding: 1rem 1.25rem;
            border-radius: 1rem;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08);
            margin-bottom: 0.75rem;
        }
        .tag {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background-color: #eff6ff;
            color: #1d4ed8;
        }
        .tag-ceo {
            background-color: #fef3c7;
            color: #c2410c;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def login_screen():
    st.title("📊 Avaliação 360 da Equipa")
    st.markdown("Uma ferramenta simples para feedback honesto e alinhamento de expectativas.")

    st.markdown("### Entrar na aplicação")
    col1, col2 = st.columns([2, 1])

    with col1:
        email = st.text_input("Email", placeholder="ex: vitor@empresa.local")
        password = st.text_input("Password", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            user = get_user_by_email(email)
            if user and verify_password(password, user["password_hash"]):
                st.session_state.user = {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                }
                st.experimental_rerun()
            else:
                st.error("Credenciais inválidas.")

    with col2:
        st.markdown("#### Utilizador de demonstração")
        st.write("Para experimentar como CEO:")
        st.code("Email: vitor@empresa.local\nPassword: 1234")
        st.caption("O CEO também é avaliado – aparece nos resultados como qualquer outra pessoa.")

def page_my_evaluations(user, period_id: int):
    st.title("📝 Minhas avaliações")

    assignments = get_assignments_for_evaluator(user["id"], period_id)
    if not assignments:
        st.info("Não tem avaliações atribuídas neste período.")
        return

    done, total = count_completed_assignments(assignments)
    progress = done / total if total else 0

    st.markdown("#### Progresso geral")
    st.progress(progress, text=f"{done} de {total} avaliações concluídas")

    options = {}
    for a in assignments:
        comps = get_competencies_for_assignment(a)
        existing = get_existing_answers(a["id"])
        is_done = comps and len(existing) == len(comps)
        label = f"{a['evaluatee_name']} {'✅' if is_done else '•'}"
        options[label] = a

    label = st.selectbox("Escolha quem quer avaliar", list(options.keys()))
    assignment = options[label]

    st.markdown(
        f"""
        <div class="card">
            <span class="tag">Avaliação 360</span>
            <h3>A avaliar: {assignment['evaluatee_name']}</h3>
            <p style="font-size: 0.85rem; color: #64748b;">
            Inclui competências comportamentais para toda a organização e competências técnicas e de objetivos
            quando partilham equipa.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    comps = get_competencies_for_assignment(assignment)
    existing = get_existing_answers(assignment["id"])

    answers = {}
    with st.form("form_avaliacao"):
        categories_labels = {
            "BEHAVIORAL": "Competências comportamentais",
            "TECHNICAL": "Competências técnicas",
            "OBJECTIVES": "Objetivos",
        }

        for cat in ["BEHAVIORAL", "TECHNICAL", "OBJECTIVES"]:
            cat_comps = [c for c in comps if c["category"] == cat]
            if not cat_comps:
                continue

            st.markdown(f"### {categories_labels[cat]}")
            for c in cat_comps:
                comp_id = c["id"]
                st.markdown(f"**{c['name']}**")
                if c["description"]:
                    st.caption(c["description"])

                cols = st.columns([1, 3])
                with cols[0]:
                    default_score = existing.get(comp_id, {}).get("score", 3)
                    score = st.slider("Pontuação", 1, 5, int(default_score), key=f"score_{comp_id}")
                with cols[1]:
                    comment_default = existing.get(comp_id, {}).get("comment", "") if existing.get(comp_id) else ""
                    comment = st.text_area(
                        "Comentário (opcional)",
                        value=comment_default,
                        key=f"comment_{comp_id}",
                    )
                st.markdown("---")
                answers[comp_id] = (score, comment)

        submitted = st.form_submit_button("💾 Guardar avaliação")
        if submitted:
            save_answers(assignment["id"], answers)
            st.success("Avaliação guardada com sucesso.")
            st.experimental_rerun()

def page_my_results(user, period_id: int):
    st.title("📈 Os meus resultados (período atual)")

    scores = get_my_scores(user["id"], period_id)
    if not scores:
        st.info("Ainda não existem resultados registados para si neste período.")
    else:
        cat_labels = {
            "BEHAVIORAL": "Comportamentais",
            "TECHNICAL": "Técnicas",
            "OBJECTIVES": "Objetivos",
        }

        st.markdown(
            """
            <div class="card">
                <span class="tag">Feedback consolidado</span>
                <p style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">
                As médias abaixo incluem as avaliações dos seus pares, líderes e, quando aplicável,
                autoavaliação. Use estes dados como ponto de partida para conversas de desenvolvimento.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(len(scores))
        for col, r in zip(cols, scores):
            with col:
                label = cat_labels.get(r["category"], r["category"])
                col.metric(label, f"{r['avg_score']:.2f} / 5")

    st.markdown("---")
    st.subheader("📊 Evolução ao longo dos períodos")

    history = get_my_scores_over_time(user["id"])
    period_names = sorted({h["period_name"] for h in history}) if history else []
    if not history or len(period_names) <= 1:
        st.info("Ainda não há histórico suficiente (é necessário ter mais do que um período com avaliações).")
        return

    df = pd.DataFrame(history)
    cat_labels = {
        "BEHAVIORAL": "Comportamentais",
        "TECHNICAL": "Técnicas",
        "OBJECTIVES": "Objetivos",
    }
    df["Categoria"] = df["category"].map(cat_labels).fillna(df["category"])

    st.dataframe(df[["period_name", "Categoria", "avg_score"]].rename(
        columns={"period_name": "Período", "avg_score": "Média"}
    ), use_container_width=True)

    for cat, g in df.groupby("Categoria"):
        st.markdown(f"#### {cat}")
        chart_df = g[["period_name", "avg_score"]].set_index("period_name")
        st.line_chart(chart_df)

def page_ceo_dashboard(period_id: int):
    st.title("📊 Painel do CEO")
    st.caption("Visão global das avaliações – incluindo o próprio CEO como avaliado.")

    scores = get_global_scores(period_id)
    if not scores:
        st.info("Ainda não existem resultados suficientes.")
        return

    df = pd.DataFrame(scores)
    cat_labels = {
        "BEHAVIORAL": "Comportamentais",
        "TECHNICAL": "Técnicas",
        "OBJECTIVES": "Objetivos",
    }
    df["Categoria"] = df["category"].map(cat_labels).fillna(df["category"])
    df.rename(columns={"evaluatee_name": "Pessoa", "avg_score": "Média"}, inplace=True)
    df = df[["Pessoa", "Categoria", "Média"]]

    st.markdown(
        """
        <div class="card">
            <span class="tag tag-ceo">Perspetiva de topo</span>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">
            Aqui vê a fotografia agregada da equipa. O CEO está incluído como avaliado, para reforçar
            uma cultura onde a liderança também é objeto de feedback.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Tabela de médias por pessoa e categoria")
    st.dataframe(df, use_container_width=True)

    st.subheader("Comparação visual (período atual)")
    pivot = df.pivot(index="Pessoa", columns="Categoria", values="Média")
    st.bar_chart(pivot)

def page_period_management():
    st.title("🗓 Gestão de períodos de avaliação")

    periods = list_periods()
    if periods:
        st.subheader("Períodos existentes")
        data = []
        for p in periods:
            data.append({
                "ID": p["id"],
                "Nome": p["name"],
                "Início": p["start_date"],
                "Fim": p["end_date"],
                "Ativo": "Sim" if p["is_active"] == 1 else "Não",
                "Nº assignments": p["n_assignments"],
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("Ainda não existem períodos definidos (já foi criado automaticamente um por defeito).")

    st.markdown("---")
    st.subheader("Criar novo período")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Nome do período", value=f"Avaliação {date.today().year}")
        start = st.date_input("Data de início", value=date.today())
    with col2:
        end = st.date_input("Data de fim", value=date.today())
        make_active = st.checkbox("Definir como período ativo", value=True)

    if st.button("Criar novo período", type="primary"):
        if end < start:
            st.error("A data de fim não pode ser anterior à data de início.")
        else:
            pid = create_period(name, str(start), str(end), make_active=make_active)
            generate_assignments_for_period(pid)
            st.success(f"Período '{name}' criado com sucesso e assignments gerados.")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Mudar período ativo")

    periods = list_periods()
    if periods:
        options = {f"{p['name']} ({p['start_date']} a {p['end_date']})": p["id"] for p in periods}
        label = st.selectbox("Escolha o período a ativar", list(options.keys()))
        target_id = options[label]
        if st.button("Tornar este período o ativo"):
            set_active_period(target_id)
            st.success("Período ativo atualizado.")
            st.experimental_rerun()
    else:
        st.info("Sem períodos disponíveis para seleção.")

# ---------- MAIN ----------

def main():
    st.set_page_config(
        page_title="Avaliação 360",
        page_icon="📊",
        layout="wide",
    )

    inject_css()
    setup_db()
    period_id = get_current_period_id()
    if period_id is not None:
        generate_assignments_for_period(period_id)

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        login_screen()
        return

    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"👤 **{user['name']}**")
        st.markdown(f"`{user['role']}`")
        if st.button("Terminar sessão", use_container_width=True):
            st.session_state.user = None
            st.experimental_rerun()

        menu = ["Minhas avaliações", "Os meus resultados"]
        if user["role"] == "CEO":
            menu.append("Painel CEO")
            menu.append("Gestão de períodos")

        choice = st.radio("Navegação", menu)

    period_id = get_current_period_id()

    if period_id is None:
        st.error("Não foi possível determinar o período ativo.")
        return

    if choice == "Minhas avaliações":
        page_my_evaluations(user, period_id)
    elif choice == "Os meus resultados":
        page_my_results(user, period_id)
    elif choice == "Painel CEO":
        page_ceo_dashboard(period_id)
    elif choice == "Gestão de períodos":
        page_period_management()

if __name__ == "__main__":
    main()
