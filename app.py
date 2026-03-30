import time
import math
import json
from datetime import datetime
from io import BytesIO

import streamlit as st
import pandas as pd
import requests
from PIL import Image

# ================== CONFIGURAÇÃO DA PÁGINA ==================
st.set_page_config(
    page_title="Transpetro Rota Fácil",
    page_icon="🚚",
    layout="wide",
)

st.title("🚚 Transpetro Rota Fácil")
st.caption("Simulador de tempo e distância rodoviária entre unidades Transpetro")

# ================== SIDEBAR ==================
try:
    mascote = Image.open("Mascote.png")
    st.sidebar.image(mascote, caption="Mascote da Área", use_container_width=True)
except Exception:
    pass

st.sidebar.header("Configurações")
api_key = st.sidebar.text_input(
    "Chave da API OpenRouteService",
    type="password",
    help="Necessária apenas quando houver cálculo de rota",
)

snap_radius = st.sidebar.number_input(
    "Raio de snapping até a via (m)",
    min_value=50,
    max_value=5000,
    value=1000,
    step=50,
    help="Aumente se o ponto estiver dentro de uma planta/área privada sem via roteável próxima",
)
units_opt = st.sidebar.selectbox("Unidade de distância", ["km", "mi"], index=0)

# Parâmetros de processamento em lote
st.sidebar.divider()
st.sidebar.subheader("Parâmetros de Lote")
CHUNK_SIZE = st.sidebar.number_input(
    "Tamanho do bloco (chunk)",
    min_value=50,
    max_value=1000,
    value=500,
    step=50,
    help="Quantidade de rotas processadas por bloco",
)
SLEEP_BASE = st.sidebar.slider(
    "Pausa entre chamadas (s)",
    min_value=0.2,
    max_value=2.0,
    value=0.4,
    step=0.1,
    help="Intervalo mínimo entre requisições à API (rate limit)",
)
SAVE_EVERY = st.sidebar.number_input(
    "Salvar parcial a cada N rotas",
    min_value=10,
    max_value=500,
    value=50,
    step=10,
    help="Frequência de gravação parcial dos resultados",
)


# ================== FUNÇÕES UTILITÁRIAS ==================
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em km pelo método de Haversine."""
    R = 6_371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def _parse_coords(value) -> float:
    """Converte string com vírgula decimal ou float para float."""
    return float(str(value).replace(",", "."))


def calcular_ors(
    lat_o: float,
    lon_o: float,
    lat_d: float,
    lon_d: float,
    api_key: str,
    snap: int = 1000,
    max_retries: int = 3,
) -> tuple[float, float, float]:
    """Chama ORS Directions (driving-car) com retry/backoff.

    Retorna (dist_km, dist_mi, tempo_min).
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Transpetro-ORS/2.0",
    }
    body = {
        "coordinates": [[float(lon_o), float(lat_o)], [float(lon_d), float(lat_d)]],
        "instructions": False,
        "radiuses": [int(snap), int(snap)],
        "units": "km",
    }

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=body, headers=headers, timeout=30)

            # Retry em caso de rate limit (429) ou erro de servidor (5xx)
            if r.status_code == 429 or r.status_code >= 500:
                wait = 2 ** attempt  # backoff exponencial: 2, 4, 8 s
                time.sleep(wait)
                last_error = Exception(
                    f"HTTP {r.status_code} na tentativa {attempt}/{max_retries}"
                )
                continue

            r.raise_for_status()
            data = r.json()

            # Verificar erro explícito da API
            if "error" in data:
                err = data["error"]
                msg = (
                    err.get("message", str(err)) if isinstance(err, dict) else str(err)
                )
                raise Exception(f"Erro da API: {msg}")

            # Suporte aos dois formatos de resposta do ORS
            if "features" in data:
                summary = data["features"][0]["properties"]["summary"]
            elif "routes" in data:
                summary = data["routes"][0]["summary"]
            else:
                raise Exception(
                    f"Formato de resposta inesperado. Chaves: {list(data.keys())}"
                )

            dist_km = round(float(summary["distance"]), 3)
            tempo_min = round(float(summary["duration"]) / 60.0, 1)
            dist_mi = round(dist_km * 0.621371, 3)
            return dist_km, dist_mi, tempo_min

        except requests.HTTPError as e:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", str(error_data))
            except Exception:
                error_msg = f"HTTP {e.response.status_code}"
            raise Exception(f"Erro HTTP: {error_msg}") from e

        except requests.ConnectionError as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise Exception(f"Falha de conexão após {max_retries} tentativas") from e

    # Se esgotou retries sem sucesso
    raise Exception(f"Falha após {max_retries} tentativas: {last_error}")


def _build_row(row, dist_km, dist_mi, tempo_min, status):
    """Monta um dicionário de resultado padronizado."""
    return {
        "Nome_Origem": row.get("Nome_Origem", "N/A"),
        "Latitude_Origem": row.get("Latitude_Origem", "N/A"),
        "Longitude_Origem": row.get("Longitude_Origem", "N/A"),
        "Nome_Destino": row.get("Nome_Destino", "N/A"),
        "Latitude_Destino": row.get("Latitude_Destino", "N/A"),
        "Longitude_Destino": row.get("Longitude_Destino", "N/A"),
        "Distancia_KM": dist_km,
        "Distancia_MI": dist_mi,
        "Tempo_Minutos": tempo_min,
        "Status": status,
        "Data_Calculo": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


def processar_rota_individual(row, api_key: str, snap: int) -> dict:
    """Processa uma única rota e retorna o dicionário de resultado."""
    try:
        lat_o = _parse_coords(row["Latitude_Origem"])
        lon_o = _parse_coords(row["Longitude_Origem"])
        lat_d = _parse_coords(row["Latitude_Destino"])
        lon_d = _parse_coords(row["Longitude_Destino"])
    except (ValueError, TypeError) as e:
        return _build_row(row, None, None, None, f"Erro coordenadas: {e}")

    # Origem = Destino?
    if haversine_km(lat_o, lon_o, lat_d, lon_d) < 0.01:
        return _build_row(row, 0, 0, 0, "Origem = Destino")

    try:
        dist_km, dist_mi, tempo_min = calcular_ors(
            lat_o, lon_o, lat_d, lon_d, api_key, snap=snap
        )
        return _build_row(row, dist_km, dist_mi, tempo_min, "Calculado")
    except Exception as e:
        return _build_row(row, None, None, None, f"Erro: {e}")


def processar_lote(
    df: pd.DataFrame,
    api_key: str,
    snap: int,
    chunk_size: int,
    sleep_base: float,
    save_every: int,
) -> pd.DataFrame:
    """Processa rotas em blocos com rate limit, backoff e persistência parcial.

    Implementa as 3 medidas do resumo técnico:
      1. Chunking — divide em blocos de `chunk_size`
      2. Rate limit — pausa `sleep_base` entre chamadas
      3. Persistência parcial — grava session_state a cada `save_every` rotas
    """
    total = len(df)
    n_chunks = math.ceil(total / chunk_size)

    # Recuperar resultados parciais de execução anterior (se houver)
    if "resultados_parciais" not in st.session_state:
        st.session_state.resultados_parciais = []

    ja_processados = len(st.session_state.resultados_parciais)
    if ja_processados > 0:
        st.info(
            f"♻️ Retomando a partir da rota {ja_processados + 1} "
            f"({ja_processados} já processadas anteriormente)."
        )

    resultados = list(st.session_state.resultados_parciais)
    progress_bar = st.progress(ja_processados / total if total > 0 else 0)
    status_text = st.empty()
    stats_container = st.empty()

    for chunk_idx in range(n_chunks):
        inicio = chunk_idx * chunk_size
        fim = min(inicio + chunk_size, total)

        # Pular rotas já processadas
        if fim <= ja_processados:
            continue

        # Ajustar início se parte do chunk já foi processada
        start_row = max(inicio, ja_processados)

        status_text.text(
            f"📦 Bloco {chunk_idx + 1}/{n_chunks}  |  "
            f"Rotas {start_row + 1}–{fim} de {total}"
        )

        for idx in range(start_row, fim):
            row = df.iloc[idx]
            resultado = processar_rota_individual(row, api_key, snap)
            resultados.append(resultado)

            # Atualizar progresso
            processados = len(resultados)
            progress_bar.progress(processados / total)

            # Persistência parcial
            if processados % save_every == 0:
                st.session_state.resultados_parciais = list(resultados)
                stats_container.caption(
                    f"💾 Salvamento parcial: {processados}/{total} rotas"
                )

            # Rate limit
            time.sleep(sleep_base)

    progress_bar.empty()
    status_text.empty()
    stats_container.empty()

    # Limpar resultados parciais após conclusão
    st.session_state.resultados_parciais = []

    return pd.DataFrame(resultados)


def gerar_template() -> pd.DataFrame:
    """Gera um DataFrame template para download."""
    return pd.DataFrame(
        {
            "Nome_Origem": ["Exemplo 1", "Exemplo 2"],
            "Latitude_Origem": [-22.9068, -23.5505],
            "Longitude_Origem": [-43.1729, -46.6333],
            "Nome_Destino": ["Exemplo Destino 1", "Exemplo Destino 2"],
            "Latitude_Destino": [-22.9035, -23.5489],
            "Longitude_Destino": [-43.2096, -46.6388],
        }
    )


def resultado_para_excel(df_resultado: pd.DataFrame) -> BytesIO:
    """Converte DataFrame de resultados em buffer Excel."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Resultados")
    buffer.seek(0)
    return buffer


def exibir_resultado_individual(dist_km, dist_mi, tempo_min, units_opt):
    """Exibe métricas de resultado de rota individual."""
    cols = st.columns(3)
    if units_opt == "mi":
        cols[0].metric("Distância (mi)", dist_mi)
        cols[1].metric("Distância (km)", dist_km)
    else:
        cols[0].metric("Distância (km)", dist_km)
        cols[1].metric("Distância (mi)", dist_mi)
    cols[2].metric("Tempo estimado (min)", tempo_min)
    st.caption(f"Cálculo realizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


def calcular_rota_individual(lat_o, lon_o, lat_d, lon_d, api_key, snap_radius, units_opt):
    """Fluxo completo de cálculo de rota individual com validações."""
    # Validar coordenadas
    try:
        lat_o_f = float(lat_o)
        lon_o_f = float(lon_o)
        lat_d_f = float(lat_d)
        lon_d_f = float(lon_d)
        if any(math.isnan(v) for v in [lat_o_f, lon_o_f, lat_d_f, lon_d_f]):
            st.error(
                "❌ Coordenadas inválidas (valores ausentes). "
                "Verifique se as unidades possuem coordenadas cadastradas."
            )
            return
    except (ValueError, TypeError):
        st.error("❌ Coordenadas inválidas. Verifique os dados de origem e destino.")
        return

    # Verificar origem = destino
    if haversine_km(lat_o_f, lon_o_f, lat_d_f, lon_d_f) < 0.01:
        st.info("✅ Origem e destino são o mesmo local (≤ 10 m). Não há deslocamento.")
        return

    if not api_key:
        st.error("⚠️ Informe a chave da API OpenRouteService na barra lateral.")
        return

    with st.spinner("Calculando rota..."):
        try:
            dist_km, dist_mi, tempo_min = calcular_ors(
                lat_o_f, lon_o_f, lat_d_f, lon_d_f, api_key, snap=snap_radius
            )
            st.success("✅ Rota calculada com sucesso!")
            exibir_resultado_individual(dist_km, dist_mi, tempo_min, units_opt)
        except Exception as e:
            st.error(f"❌ Erro ao calcular rota: {e}")


# ================== CARGA DAS BASES ==================
@st.cache_data
def carregar_base():
    """Carrega e junta as bases de centros e coordenadas."""
    for enc in ("utf-8", "latin-1", "ISO-8859-1"):
        try:
            centros = pd.read_csv("nomes e localização.csv", sep=";", encoding=enc)
            break
        except (UnicodeDecodeError, FileNotFoundError):
            centros = None

    for enc in ("utf-8", "latin-1", "ISO-8859-1"):
        try:
            coords = pd.read_csv("coordenadas_consolidadas.csv", encoding=enc)
            break
        except (UnicodeDecodeError, FileNotFoundError):
            coords = None

    if centros is None or coords is None:
        return None, {}

    base = centros.merge(coords, on="Centro", how="left")
    base["label"] = (
        base["Centro"] + " – " + base["Denominação"] + " (" + base["Local"] + ")"
    )
    label_map = {row["label"]: row for _, row in base.iterrows()}
    return base, label_map


base, label_to_row = carregar_base()

# ================== MODO DE ENTRADA ==================
modo = st.radio(
    "Modo de entrada",
    [
        "Usar base de Centros Transpetro",
        "Informar manualmente",
        "Processar lote (Upload de arquivo)",
    ],
)
st.divider()

# ================== PROCESSAMENTO EM LOTE ==================
if modo == "Processar lote (Upload de arquivo)":
    st.subheader("📋 Processamento em Lote")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("**1. Baixe o template:**")
        template = gerar_template()
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            template.to_excel(writer, index=False, sheet_name="Template")
        buffer.seek(0)
        st.download_button(
            label="📥 Baixar Template Excel",
            data=buffer,
            file_name="template_rotas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col2:
        st.write("**2. Preencha o template com suas rotas**")
        st.caption(
            "Colunas obrigatórias: Nome_Origem, Latitude_Origem, Longitude_Origem, "
            "Nome_Destino, Latitude_Destino, Longitude_Destino"
        )

    st.write("**3. Faça o upload do arquivo preenchido:**")
    uploaded_file = st.file_uploader(
        "Escolha o arquivo Excel ou CSV",
        type=["xlsx", "xls", "csv"],
        help="Arquivo deve conter as colunas do template",
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)

            st.success(f"✅ Arquivo carregado! {len(df_upload)} rotas encontradas.")

            with st.expander("📊 Visualizar dados carregados"):
                st.dataframe(df_upload)

            # Validar colunas
            colunas_obrigatorias = [
                "Nome_Origem",
                "Latitude_Origem",
                "Longitude_Origem",
                "Nome_Destino",
                "Latitude_Destino",
                "Longitude_Destino",
            ]
            colunas_faltantes = [
                c for c in colunas_obrigatorias if c not in df_upload.columns
            ]

            if colunas_faltantes:
                st.error(f"❌ Colunas faltantes: {', '.join(colunas_faltantes)}")
            elif not api_key:
                st.warning(
                    "⚠️ Informe a chave da API OpenRouteService na barra lateral."
                )
            else:
                # Estimativa de tempo
                est_min = len(df_upload) * SLEEP_BASE / 60
                st.info(
                    f"⏱️ Tempo estimado: ~{est_min:.0f} min "
                    f"({len(df_upload)} rotas × {SLEEP_BASE}s de pausa). "
                    f"Blocos de {CHUNK_SIZE} rotas com salvamento a cada {SAVE_EVERY}."
                )

                # Botão de retomada se houver parciais
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    btn_calcular = st.button("🚚 Calcular Todas as Rotas", type="primary")
                with col_btn2:
                    if (
                        "resultados_parciais" in st.session_state
                        and len(st.session_state.resultados_parciais) > 0
                    ):
                        n_parciais = len(st.session_state.resultados_parciais)
                        btn_limpar = st.button(
                            f"🗑️ Limpar parciais ({n_parciais} rotas)"
                        )
                        if btn_limpar:
                            st.session_state.resultados_parciais = []
                            st.rerun()

                if btn_calcular:
                    df_resultados = processar_lote(
                        df_upload,
                        api_key,
                        snap_radius,
                        CHUNK_SIZE,
                        SLEEP_BASE,
                        SAVE_EVERY,
                    )

                    st.success(
                        f"✅ Concluído! {len(df_resultados)} rotas processadas."
                    )

                    # Resultados
                    st.subheader("📊 Resultados")
                    st.dataframe(df_resultados)

                    # Estatísticas
                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        "Rotas Calculadas",
                        len(df_resultados[df_resultados["Status"] == "Calculado"]),
                    )
                    col2.metric(
                        "Origem = Destino",
                        len(
                            df_resultados[
                                df_resultados["Status"] == "Origem = Destino"
                            ]
                        ),
                    )
                    col3.metric(
                        "Erros",
                        len(
                            df_resultados[
                                df_resultados["Status"].str.contains("Erro", na=False)
                            ]
                        ),
                    )

                    # Downloads
                    st.subheader("📥 Downloads")
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📊 Baixar Resultados (Excel)",
                            data=resultado_para_excel(df_resultados),
                            file_name=f"resultados_rotas_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    with col_dl2:
                        st.download_button(
                            label="📊 Baixar Resultados (JSON)",
                            data=df_resultados.to_json(
                                orient="records", date_format="iso"
                            ),
                            file_name=f"resultados_rotas_{datetime.now():%Y%m%d_%H%M%S}.json",
                            mime="application/json",
                        )

        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {e}")

# ================== USAR BASE TRANSPETRO ==================
elif modo == "Usar base de Centros Transpetro":
    if base is None:
        st.error(
            "❌ Arquivos de base não encontrados. Verifique se "
            "'nomes e localização.csv' e 'coordenadas_consolidadas.csv' "
            "estão no diretório do app."
        )
    else:
        col1, col2 = st.columns(2)
        with col1:
            origem_label = st.selectbox("Origem", sorted(label_to_row.keys()))
            origem = label_to_row[origem_label]
            st.caption(f"UO: {origem['UO']}")
        with col2:
            destino_label = st.selectbox("Destino", sorted(label_to_row.keys()))
            destino = label_to_row[destino_label]
            st.caption(f"UO: {destino['UO']}")

        st.divider()
        if st.button("🚚 Calcular Rota"):
            calcular_rota_individual(
                origem["Latitude"],
                origem["Longitude"],
                destino["Latitude"],
                destino["Longitude"],
                api_key,
                snap_radius,
                units_opt,
            )

# ================== MODO MANUAL ==================
else:
    col1, col2 = st.columns(2)
    with col1:
        nome_o = st.text_input("Nome Origem")
        lat_o = st.number_input("Latitude Origem", format="%.8f")
        lon_o = st.number_input("Longitude Origem", format="%.8f")
    with col2:
        nome_d = st.text_input("Nome Destino")
        lat_d = st.number_input("Latitude Destino", format="%.8f")
        lon_d = st.number_input("Longitude Destino", format="%.8f")

    st.divider()
    if st.button("🚚 Calcular Rota"):
        if lat_o == 0 and lon_o == 0 and lat_d == 0 and lon_d == 0:
            st.warning("⚠️ Informe as coordenadas de origem e destino.")
        else:
            calcular_rota_individual(
                lat_o, lon_o, lat_d, lon_d, api_key, snap_radius, units_opt
            )
