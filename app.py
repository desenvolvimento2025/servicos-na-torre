"""
Serviços na Torre — protótipo do webapp de ticket de atendimento e
monitoramento de serviços logísticos.

Como rodar (via cmd):
    pip install -r requirements.txt
    streamlit run app.py

Por padrão o app lê as planilhas REAIS da pasta OneDrive (ver
src/config.py). Para testar com dados fictícios em vez da pasta real,
rode antes "python gerar_exemplos.py" e defina a variável de ambiente
SERVICOS_TORRE_PASTA apontando para a pasta data/entrada (ver README.md).
"""
import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

from src import config, database, tempo
from src.scheduler import iniciar_rotinas_em_background

st.set_page_config(
    page_title="Serviços na Torre",
    page_icon="🗼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Aparência: cores/tema em .streamlit/config.toml; aqui só alguns retoques
# de layout (cantos arredondados, espaçamento, cabeçalho da barra lateral).
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stSidebarContent"] { padding-top: 1.5rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
    }
    div[data-testid="stAlert"] { border-radius: 10px; }
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 8px;
    }
    .torre-titulo {
        font-size: 1.4rem;
        font-weight: 700;
        border-bottom: 3px solid #F97316;
        padding-bottom: 0.4rem;
        margin-bottom: 0.8rem;
        display: inline-block;
    }
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cores dos status controlados pelo webapp (STATUS_MONITOR).
CORES_STATUS_MONITOR = {
    "PENDENTE": ("#7C2D12", "#FDBA74"),   # fundo, texto
    "ABERTO": ("#14532D", "#86EFAC"),
}


def badge_status(valor):
    """HTML de uma pílula colorida para o STATUS_MONITOR (PENDENTE/ABERTO)."""
    fundo, texto = CORES_STATUS_MONITOR.get(valor, ("#334155", "#E2E8F0"))
    rotulo = valor or "—"
    return (
        f'<span class="status-badge" style="background:{fundo}; color:{texto};">'
        f"{rotulo}</span>"
    )


def _tempo_sem_vinculo(criado_em_str):
    """Formata (agora - criado_em) como 'Xh Ymin'. criado_em é gravado no
    formato '%Y-%m-%d %H:%M:%S' (ver database._now_str)."""
    if not criado_em_str:
        return "?"
    try:
        criado_em = datetime.strptime(criado_em_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "?"
    total_min = max(int((tempo.agora() - criado_em).total_seconds() // 60), 0)
    horas, minutos = divmod(total_min, 60)
    return f"{horas}h {minutos:02d}min"

# ---------------------------------------------------------------------------
# Inicialização (idempotente a cada rerun do Streamlit)
# ---------------------------------------------------------------------------
iniciar_rotinas_em_background()

# Atualiza a tela sozinha a cada 5 minutos (sem precisar apertar F5). Como a
# importação das planilhas roda em background a cada 30 minutos (múltiplo de
# 5), cada atualização automática já reflete os dados mais recentes assim
# que a importação seguinte acontecer.
#
# IMPORTANTE (limitação do navegador, não do app): este timer de 5 min só
# "tique-taca" enquanto a aba está em primeiro plano. Todo navegador
# (Chrome, Edge, Safari, e principalmente no celular) pausa/limita
# JavaScript de abas em segundo plano ou com a tela bloqueada, para
# economizar bateria — isso vale para qualquer site, não só para este app,
# e não existe código que contorne isso. Os dados no servidor continuam
# sendo importados a cada 30 min mesmo sem ninguém com a tela aberta (ver
# src/scheduler.py); o que garantimos aqui é que, assim que a pessoa VOLTAR
# a olhar para a aba (mesmo que ela tenha ficado minimizada, em segundo
# plano, ou o celular bloqueado por horas), a página recarrega na hora e
# mostra os dados mais atuais — em vez de esperar até 5 minutos parada.
#
# Fica dentro da barra lateral (mesmo sem UI visível ali) só para não deixar
# "buraco" vazio acima da grade principal: cada componente invisível ainda
# reserva um respiro mínimo no bloco onde é colocado, e a barra lateral não
# tem relação com o espaço da tela principal.
with st.sidebar:
    st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh_5min")

    components.html(
        """
        <script>
        (function() {
            var ficouOculta = false;
            document.addEventListener("visibilitychange", function() {
                if (document.visibilityState === "hidden") {
                    ficouOculta = true;
                } else if (document.visibilityState === "visible" && ficouOculta) {
                    // Recarrega a página inteira assim que o usuário volta a
                    // olhar para a aba (troca de app, minimizou, celular
                    // bloqueado etc.), garantindo dados atuais na hora.
                    window.parent.location.reload();
                }
            });
        })();
        </script>
        """,
        height=0,
    )

if "primeira_carga_feita" not in st.session_state:
    servicos_existentes = database.listar_servicos()
    if not servicos_existentes:
        database.importar_tudo()
    st.session_state["primeira_carga_feita"] = True

if "servico_selecionado" not in st.session_state:
    st.session_state["servico_selecionado"] = None
if "banner_dismissed_until" not in st.session_state:
    st.session_state["banner_dismissed_until"] = None
if "usuario_atual" not in st.session_state:
    st.session_state["usuario_atual"] = None
if "ver_detalhe_completo" not in st.session_state:
    st.session_state["ver_detalhe_completo"] = None

# Modo "somente banner" (?modo=banner na URL): uma cópia interativa, idêntica
# em funcionamento, mostrando SÓ o aviso de vínculo — pensada para abrir numa
# janela/aba separada (computador ou celular) e deixar sempre visível, já
# que não é possível um site "puxar" sozinho a janela principal para a
# frente da tela (bloqueio de segurança de todo navegador).
modo_banner = st.query_params.get("modo") == "banner"

nomes_programadores = [u["nome"] for u in database.listar_programadores()]

# ---------------------------------------------------------------------------
# Barra lateral: identificação do Programador + menus discretos (itens 3 e 4)
# ---------------------------------------------------------------------------
if not modo_banner:
    with st.sidebar:
        st.markdown('<span class="torre-titulo">🗼 Serviços na Torre</span>', unsafe_allow_html=True)

        usuarios = database.listar_usuarios()
        st.session_state["usuario_atual"] = st.selectbox(
            "Quem é você?",
            options=["—"] + nomes_programadores,
            index=0 if not st.session_state["usuario_atual"]
            else (["—"] + nomes_programadores).index(st.session_state["usuario_atual"]),
            help="Sem login por enquanto — qualquer pessoa pode abrir o webapp. "
            "Selecione seu nome apenas para identificar seus comentários e vínculos. "
            "Lista filtrada pela coluna PROGRAMADOR = SIM da planilha de Usuários.",
        )

        if st.button("🔄 Importar planilhas agora", use_container_width=True):
            resultado = database.importar_tudo()
            st.success(f"Importado: {resultado['novos']} novo(s), {resultado['atualizados']} atualizado(s).")
            st.rerun()

        st.divider()

        # Menus secundários (itens 3 e 4) — sempre ocultos/recolhidos ao abrir
        # o webapp; só abrem se o usuário clicar.
        with st.expander(f"👤 Usuários ({len(usuarios)})", expanded=False):
            st.dataframe(pd.DataFrame(usuarios), hide_index=True, use_container_width=True, height=250)

        with st.expander("🏷️ Status", expanded=False):
            st.dataframe(pd.DataFrame(database.listar_status()), hide_index=True, use_container_width=True)

        st.caption(
            "Fonte dos dados (planilhas Excel): \n\n" + config.PASTA_PLANILHAS
        )

        st.divider()
        st.markdown(
            '<a href="?modo=banner" target="_blank">🔔 Abrir aviso de vínculo em janela separada</a>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Abre uma cópia só com o aviso de serviço sem Programador, para "
            "deixar fixada numa outra janela/aba (computador ou celular)."
        )

# ---------------------------------------------------------------------------
# Banner: serviços sem Programador vinculado (item 7)
# ---------------------------------------------------------------------------
pendentes = database.servicos_sem_programador()
ids_pendentes = [p["id_atendimento"] for p in pendentes]
agora = tempo.agora()
mostrar_banner = bool(pendentes) and (
    st.session_state["banner_dismissed_until"] is None
    or agora >= st.session_state["banner_dismissed_until"]
)

# Notificação nativa do navegador (fora da aba/janela) quando surge um
# serviço NOVO sem Programador — o mais perto que dá de "trazer para a
# frente da tela" sem depender do usuário estar olhando para a aba: o
# navegador desenha esse aviso por cima de qualquer outro programa aberto
# no computador, e no celular ele aparece na barra de notificações,
# ENQUANTO o navegador/aba continuar aberto (sem estar fechado ou o
# celular bloqueado, limitação de bateria do próprio sistema, explicada
# antes). Guarda em localStorage os ids já notificados, para não repetir
# a mesma notificação a cada rerun/atualização de 5 min. Fica na barra
# lateral pelo mesmo motivo dos componentes acima: não empurrar a grade
# principal para baixo com espaço vazio.
with st.sidebar:
    components.html(
        f"""
        <script>
        (function() {{
            const idsPendentesAgora = {json.dumps(ids_pendentes)};
            const CHAVE = "torre_ids_ja_notificados";

            function pedirPermissao() {{
                if (window.Notification && Notification.permission !== "granted"
                    && Notification.permission !== "denied") {{
                    Notification.requestPermission();
                }}
            }}

            function verificarNovosPendentes() {{
                if (!window.Notification || Notification.permission !== "granted") return;
                let jaNotificados = [];
                try {{
                    jaNotificados = JSON.parse(window.parent.localStorage.getItem(CHAVE) || "[]");
                }} catch (e) {{ jaNotificados = []; }}
                const novos = idsPendentesAgora.filter(id => !jaNotificados.includes(id));
                if (novos.length > 0) {{
                    new Notification("🗼 Serviços na Torre", {{
                        body: novos.length === 1
                            ? `Serviço ${{novos[0]}} está aguardando um Programador.`
                            : `${{novos.length}} serviços novos aguardando um Programador.`,
                        tag: "torre-pendentes",
                    }});
                }}
                try {{
                    window.parent.localStorage.setItem(
                        CHAVE, JSON.stringify(idsPendentesAgora)
                    );
                }} catch (e) {{}}
            }}

            // Expõe um botão global "Ativar notificações" (criado pelo Python
            // logo abaixo) para pedir a permissão com um clique real do
            // usuário — a maioria dos navegadores exige isso.
            window.parent.__torreAtivarNotificacoes = pedirPermissao;
            verificarNovosPendentes();
        }})();
        </script>
        """,
        height=0,
    )

if modo_banner:
    st.markdown('<span class="torre-titulo">🔔 Aviso de vínculo — Serviços na Torre</span>', unsafe_allow_html=True)
    st.markdown(
        """
        <button onclick="window.__torreAtivarNotificacoes && window.__torreAtivarNotificacoes()"
        style="margin-bottom:0.75rem;">🔔 Ativar notificações do navegador</button>
        """,
        unsafe_allow_html=True,
    )
    if not pendentes:
        st.success("✅ Nenhum serviço aguardando Programador no momento.")

if mostrar_banner:
    with st.container(border=True):
        st.warning(
            f"⚠️ Há {len(pendentes)} serviço(s) aguardando um Programador. "
            "Este aviso volta a aparecer a cada 5 minutos até todos serem preenchidos."
        )

        # Se acabamos de excluir um vínculo, o serviço que virou pendente
        # agora pode não ser o mesmo que já estava escolhido neste combo
        # (que guarda a última seleção). Sem isso, o primeiro clique em
        # "Vincular" aqui podia acabar vinculando OUTRO serviço da lista,
        # dando a impressão de que a ação "não colou" da primeira vez.
        # Por isso, força o combo a já vir com o serviço recém-excluído
        # selecionado.
        alvo_recente = st.session_state.get("manter_selecionado_apos_acao")
        if alvo_recente in ids_pendentes:
            st.session_state["banner_servico"] = alvo_recente

        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            def _rotulo_servico_pendente(i):
                p = next(p for p in pendentes if p["id_atendimento"] == i)
                tipo_servico = p["tipo_servico"] or "sem tipo"
                percurso = p["percurso"] or "sem percurso"
                sem_vinculo = _tempo_sem_vinculo(p["criado_em"])
                # "há Xh Ymin sem Programador" logo no início, para não ser
                # cortado quando o texto do combo não cabe todo na largura.
                return f"{i} — há {sem_vinculo} sem Programador — {tipo_servico} — {percurso}"

            servico_escolhido = st.selectbox(
                "Serviço", options=ids_pendentes,
                format_func=_rotulo_servico_pendente,
                key="banner_servico",
            )
        with col2:
            programador_escolhido = st.selectbox(
                "Programador responsável", options=nomes_programadores, key="banner_programador",
            )
        with col3:
            st.write("")
            st.write("")
            if st.button("Vincular", type="primary", use_container_width=True):
                database.vincular_programador(servico_escolhido, programador_escolhido)
                st.rerun()
        if st.button("Fechar por 5 minutos"):
            st.session_state["banner_dismissed_until"] = agora + timedelta(
                seconds=config.INTERVALO_BANNER_SEGUNDOS
            )
            st.rerun()

# O divisor só aparece junto com o banner (separando aviso da grade). Sem
# vínculo pendente (ou banner fechado por 5 min), não faz sentido reservar
# essa linha/espaço — a grade de Serviços sobe e ocupa a tela toda.
if mostrar_banner:
    st.divider()

# ---------------------------------------------------------------------------
# Segunda tela: todos os demais dados do serviço (as ~80 colunas do Koepe
# que não aparecem na grade principal). Só é aberta pelo botão "Ver todos
# os dados do serviço"; para voltar, usa o botão "← Voltar para a lista".
# ---------------------------------------------------------------------------
if st.session_state["ver_detalhe_completo"] is not None:
    id_detalhe = st.session_state["ver_detalhe_completo"]
    servico_detalhe, _ = database.obter_servico(id_detalhe)

    if st.button("← Voltar para a lista"):
        st.session_state["ver_detalhe_completo"] = None
        st.rerun()

    if servico_detalhe is None:
        st.error("Serviço não encontrado.")
    else:
        st.subheader(
            f"Serviço {servico_detalhe['id_atendimento']} — "
            f"{servico_detalhe.get('solicitante') or 'sem solicitante'}"
        )

        campos_ja_mostrados = {c for c, _ in config.COLUNAS_GRADE_PRINCIPAL} | {
            "campos_extra", "criado_em", "atualizado_em"
        }
        demais_campos = [k for k in servico_detalhe.keys() if k not in campos_ja_mostrados]

        st.markdown("##### Demais dados do serviço")
        for campo in demais_campos:
            valor = servico_detalhe.get(campo)
            if valor in (None, ""):
                continue
            st.text(f"{campo}: {valor}")

        import json as _json
        extras = servico_detalhe.get("campos_extra")
        if extras:
            try:
                extras_dict = _json.loads(extras)
            except Exception:
                extras_dict = {}
            for k, v in extras_dict.items():
                if v not in (None, ""):
                    st.text(f"{k}: {v}")

    st.stop()

# ---------------------------------------------------------------------------
# Tela principal: a grade fica sempre visível. Clicar em um registro (marcar
# a caixinha da linha) abre o histórico de Comentários e o vínculo de
# Programador logo abaixo da grade, sem navegar para outra página.
# ---------------------------------------------------------------------------
st.markdown('<span class="torre-titulo">Serviços</span>', unsafe_allow_html=True)

servicos = database.listar_servicos()
if not servicos:
    st.info("Nenhum serviço importado ainda. Use 'Importar planilhas agora' na barra lateral.")
else:
    colunas = config.COLUNAS_GRADE_PRINCIPAL
    df = pd.DataFrame(servicos)
    for campo, _ in colunas:
        if campo not in df.columns:
            df[campo] = None
    df_grade = df[[c for c, _ in colunas]].rename(
        columns={c: label for c, label in colunas}
    )

    def _cor_status_monitor(valor):
        fundo, texto = CORES_STATUS_MONITOR.get(valor, (None, None))
        return f"background-color: {fundo}; color: {texto};" if fundo else ""

    def _cor_urgente(valor):
        if str(valor).strip().lower() in ("sim", "yes", "true"):
            return "background-color: #7F1D1D; color: #FECACA;"
        return ""

    grade_estilizada = df_grade.style.map(
        _cor_status_monitor, subset=["STATUS_MONITOR"]
    ).map(_cor_urgente, subset=["Urgente"])

    evento = st.dataframe(
        grade_estilizada,
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    linhas_sel = evento.selection.rows if evento and evento.selection else []
    if linhas_sel:
        st.session_state["servico_selecionado"] = df.iloc[linhas_sel[0]]["id_atendimento"]
    else:
        st.session_state["servico_selecionado"] = None

    # Depois de trocar ou excluir um vínculo, mantém a janela do MESMO
    # serviço aberta (não depende da grade ter guardado a seleção) — assim
    # o resultado da ação já aparece na hora, sem precisar procurar o
    # serviço certo em meio a outros pendentes.
    if st.session_state.get("manter_selecionado_apos_acao") is not None:
        st.session_state["servico_selecionado"] = st.session_state.pop("manter_selecionado_apos_acao")

    if st.session_state["servico_selecionado"] is not None:
        id_sel = st.session_state["servico_selecionado"]
        servico, comentarios = database.obter_servico(id_sel)

        if servico is not None:
            with st.container(border=True):
                col_titulo, col_botao = st.columns([4, 2])
                with col_titulo:
                    st.markdown(
                        f"**Serviço {servico['id_atendimento']} — "
                        f"{servico.get('solicitante') or 'sem solicitante'}** "
                        + badge_status(servico.get("status_monitor")),
                        unsafe_allow_html=True,
                    )
                with col_botao:
                    if st.button(
                        "📋 Ver todos os dados do serviço",
                        key=f"ver_detalhe_{id_sel}",
                        use_container_width=True,
                    ):
                        st.session_state["ver_detalhe_completo"] = id_sel
                        st.rerun()

                # Vincular Programador — a única ação disponível aqui.
                if not servico.get("programador"):
                    with st.form(f"form_vincular_{id_sel}"):
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            programador_escolhido = st.selectbox(
                                "Programador responsável", options=nomes_programadores
                            )
                        with col_b:
                            st.write("")
                            st.write("")
                            enviado = st.form_submit_button("Vincular", type="primary", use_container_width=True)
                        if enviado:
                            database.vincular_programador(id_sel, programador_escolhido)
                            st.rerun()
                else:
                    st.caption(
                        f"Vinculado a **{servico['programador']}** em {servico.get('data_hora_vinculo') or ''}."
                    )
                    col_troca_sel, col_troca_btn, col_excluir = st.columns([3, 2, 2])
                    with col_troca_sel:
                        novo_programador = st.selectbox(
                            "Trocar para",
                            options=nomes_programadores,
                            key=f"trocar_sel_{id_sel}",
                            label_visibility="collapsed",
                        )
                    with col_troca_btn:
                        if st.button(
                            "🔁 Trocar Programador",
                            key=f"trocar_btn_{id_sel}",
                            use_container_width=True,
                        ):
                            database.trocar_programador(id_sel, novo_programador)
                            st.session_state["manter_selecionado_apos_acao"] = id_sel
                            st.rerun()
                    with col_excluir:
                        if st.button(
                            "❌ Excluir vínculo",
                            key=f"excluir_vinculo_{id_sel}",
                            use_container_width=True,
                        ):
                            database.reverter_vinculo(id_sel)
                            st.session_state["manter_selecionado_apos_acao"] = id_sel
                            st.rerun()

                # Histórico de Comentários — mais recente primeiro, só o
                # texto do histórico, 1 linha por comentário (sem ícone,
                # autor ou timestamp separados). O tempo decorrido até o
                # comentário anterior entra na MESMA linha, logo à frente do
                # horário já registrado no texto (mantém 1 linha por
                # atualização, sem linha extra de legenda).
                st.markdown(f"###### 💬 Comentários ({len(comentarios)})")
                for i, c in enumerate(comentarios):
                    linha = c["texto"]
                    if i + 1 < len(comentarios):
                        try:
                            data_atual = datetime.strptime(c["data_hora"], "%Y-%m-%d %H:%M:%S")
                            data_anterior = datetime.strptime(
                                comentarios[i + 1]["data_hora"], "%Y-%m-%d %H:%M:%S"
                            )
                            duracao = database.formatar_duracao(
                                (data_atual - data_anterior).total_seconds()
                            )
                            linha = f"{linha} (⏱️ {duracao} desde o anterior)"
                        except (TypeError, ValueError):
                            pass
                    st.text(linha)

                autor_atual = st.session_state["usuario_atual"] or "Usuário"
                novo_comentario = st.text_area("Adicionar comentário manual", key=f"comentario_{id_sel}")
                if st.button("Enviar comentário", key=f"enviar_comentario_{id_sel}"):
                    if novo_comentario.strip():
                        database.adicionar_comentario_manual(id_sel, autor_atual, novo_comentario.strip())
                        st.rerun()
