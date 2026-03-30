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

# ================== INTERNACIONALIZAÇÃO ==================
TRANSLATIONS = {
    "pt": {
        # Títulos e captions
        "app_title": "🚚 Transpetro Rota Fácil",
        "app_caption": "Simulador de tempo e distância rodoviária entre unidades Transpetro",
        # Sidebar — Configurações
        "sidebar_settings": "⚙️ Configurações",
        "sidebar_language": "🌐 Idioma / Language",
        "sidebar_api_engine": "Motor de API",
        "sidebar_ors_label": "OpenRouteService (ORS)",
        "sidebar_google_label": "Google Maps",
        "sidebar_api_key_ors": "Chave da API — OpenRouteService",
        "sidebar_api_key_google": "Chave da API — Google Maps",
        "sidebar_api_key_help_ors": "Obtenha gratuitamente em openrouteservice.org",
        "sidebar_api_key_help_google": "Obtenha no Google Cloud Console (Distance Matrix API)",
        "sidebar_api_tip": (
            "💡 **Dica de volume:** Para grandes lotes (> 500 rotas), "
            "prefira o **Google Maps** — mais rápido e robusto para alto volume. "
            "O ORS é ideal para até ~500 rotas/dia (plano gratuito)."
        ),
        "sidebar_api_validating": "Validando chave...",
        "sidebar_api_valid_ors": "✅ Chave ORS válida",
        "sidebar_api_valid_google": "✅ Chave Google válida",
        "sidebar_api_invalid": "❌ Chave inválida ou sem permissão",
        "sidebar_snap": "Raio de snapping até a via (m)",
        "sidebar_snap_help": "Aumente se o ponto estiver dentro de uma área privada sem via próxima",
        "sidebar_units": "Unidade de distância",
        "sidebar_batch_params": "Parâmetros de Lote",
        "sidebar_chunk": "Tamanho do bloco (chunk)",
        "sidebar_chunk_help": "Rotas processadas por bloco",
        "sidebar_sleep": "Pausa entre chamadas (s)",
        "sidebar_sleep_help": "Intervalo entre requisições (rate limit)",
        "sidebar_save_every": "Salvar parcial a cada N rotas",
        "sidebar_save_every_help": "Frequência de salvamento parcial",
        # Sidebar — Sobre
        "sidebar_about": "📋 Sobre o Software",
        "sidebar_software_name": "Transpetro Rota Fácil",
        "sidebar_version": "Versão 3.0",
        "sidebar_inpi": "INPI: BR5120260XXXXX-X",  # placeholder
        "sidebar_authors_label": "👥 Autores",
        "sidebar_authors": [
          '<a href="https://www.linkedin.com/in/andersonportella" target="_blank">Anderson Portella</a> — UFF — andersonportella@yahoo.com.br',
          '<a href="https://www.linkedin.com/in/robsonsouza77/" target="_blank">Robson Ferreira de Souza</a> — IME — souzarbsn@gmail.com',
          '<a href="https://www.linkedin.com/in/profmarcosdossantos/" target="_blank">Prof. Dr. Marcos dos Santos</a> — Escola Naval — marcos.santos@marinha.mil.br',
          '<a href="https://www.linkedin.com/in/carlos-francisco-sim%C3%B5es-gomes-0906a944" target="_blank">Prof. Dr. Carlos Francisco Simões Gomes</a> — UFF — carlos_gomes@id.uff.br',
        ],
        "sidebar_links": "🔗 Links",
        "sidebar_manual": "📖 Manual do Usuário",
        "sidebar_citation": "📝 Como Citar",
        "sidebar_support": "🛠️ Suporte",
        # Citações
        "citation_title": "📝 Formatos de Citação",
        "citation_abnt": "ABNT",
        "citation_apa": "APA",
        "citation_software": "Software (INPI)",
        # Modos de entrada
        "mode_label": "Modo de entrada",
        "mode_base": "Usar base de Centros Transpetro",
        "mode_manual": "Informar manualmente",
        "mode_batch": "Processar lote (Upload de arquivo)",
        # Base Transpetro
        "origin_label": "Origem",
        "dest_label": "Destino",
        "uo_label": "UO",
        "calc_button": "🚚 Calcular Rota",
        "base_not_found": (
            "❌ Arquivos de base não encontrados. Verifique se "
            "'nomes e localização.csv' e 'coordenadas_consolidadas.csv' "
            "estão no diretório do app."
        ),
        # Manual
        "manual_origin": "Nome Origem",
        "manual_lat_o": "Latitude Origem",
        "manual_lon_o": "Longitude Origem",
        "manual_dest": "Nome Destino",
        "manual_lat_d": "Latitude Destino",
        "manual_lon_d": "Longitude Destino",
        "manual_coords_warning": "⚠️ Informe as coordenadas de origem e destino.",
        # Batch
        "batch_title": "📋 Processamento em Lote",
        "batch_download_template": "📥 Baixar Template Excel",
        "batch_step1": "**1. Baixe o template:**",
        "batch_step2": "**2. Preencha o template com suas rotas**",
        "batch_step2_caption": (
            "Colunas obrigatórias: Nome_Origem, Latitude_Origem, Longitude_Origem, "
            "Nome_Destino, Latitude_Destino, Longitude_Destino"
        ),
        "batch_step3": "**3. Faça o upload do arquivo preenchido:**",
        "batch_upload_label": "Escolha o arquivo Excel ou CSV",
        "batch_upload_help": "Arquivo deve conter as colunas do template",
        "batch_loaded": "✅ Arquivo carregado! {} rotas encontradas.",
        "batch_view_data": "📊 Visualizar dados carregados",
        "batch_missing_cols": "❌ Colunas faltantes: {}",
        "batch_no_key": "⚠️ Informe e valide a chave da API na barra lateral.",
        "batch_time_estimate": (
            "⏱️ Tempo estimado: ~{:.0f} min "
            "({} rotas × {}s de pausa). "
            "Blocos de {} rotas com salvamento a cada {}."
        ),
        "batch_calc_button": "🚚 Calcular Todas as Rotas",
        "batch_clear_partial": "🗑️ Limpar parciais ({} rotas)",
        "batch_resuming": "♻️ Retomando a partir da rota {} ({} já processadas anteriormente).",
        "batch_done": "✅ Concluído! {} rotas processadas.",
        "batch_results_title": "📊 Resultados",
        "batch_stats_calc": "Rotas Calculadas",
        "batch_stats_same": "Origem = Destino",
        "batch_stats_err": "Erros",
        "batch_downloads": "📥 Downloads",
        "batch_dl_excel": "📊 Baixar Resultados (Excel)",
        "batch_dl_json": "📊 Baixar Resultados (JSON)",
        "batch_error": "❌ Erro ao processar arquivo: {}",
        # Resultado individual
        "result_dist_km": "Distância (km)",
        "result_dist_mi": "Distância (mi)",
        "result_time": "Tempo estimado (min)",
        "result_calc_at": "Cálculo realizado em: {}",
        "result_success": "✅ Rota calculada com sucesso!",
        "result_same_place": "✅ Origem e destino são o mesmo local (≤ 10 m). Não há deslocamento.",
        # Erros
        "err_invalid_coords": "❌ Coordenadas inválidas (valores ausentes).",
        "err_invalid_coords2": "❌ Coordenadas inválidas. Verifique os dados.",
        "err_no_key": "⚠️ Informe e valide a chave da API na barra lateral.",
        "err_calc": "❌ Erro ao calcular rota: {}",
        "spinner_calc": "Calculando rota...",
    },
    "en": {
        "app_title": "🚚 Transpetro Easy Route",
        "app_caption": "Road time and distance simulator between Transpetro units",
        "sidebar_settings": "⚙️ Settings",
        "sidebar_language": "🌐 Language / Idioma",
        "sidebar_api_engine": "API Engine",
        "sidebar_ors_label": "OpenRouteService (ORS)",
        "sidebar_google_label": "Google Maps",
        "sidebar_api_key_ors": "API Key — OpenRouteService",
        "sidebar_api_key_google": "API Key — Google Maps",
        "sidebar_api_key_help_ors": "Get it free at openrouteservice.org",
        "sidebar_api_key_help_google": "Get it at Google Cloud Console (Distance Matrix API)",
        "sidebar_api_tip": (
            "💡 **Volume tip:** For large batches (> 500 routes), "
            "prefer **Google Maps** — faster and more robust for high volume. "
            "ORS is ideal for up to ~500 routes/day (free plan)."
        ),
        "sidebar_api_validating": "Validating key...",
        "sidebar_api_valid_ors": "✅ ORS key valid",
        "sidebar_api_valid_google": "✅ Google key valid",
        "sidebar_api_invalid": "❌ Invalid key or insufficient permission",
        "sidebar_snap": "Snapping radius to road (m)",
        "sidebar_snap_help": "Increase if the point is inside a private area with no nearby road",
        "sidebar_units": "Distance unit",
        "sidebar_batch_params": "Batch Parameters",
        "sidebar_chunk": "Chunk size",
        "sidebar_chunk_help": "Routes processed per chunk",
        "sidebar_sleep": "Pause between calls (s)",
        "sidebar_sleep_help": "Interval between API requests (rate limit)",
        "sidebar_save_every": "Save partial every N routes",
        "sidebar_save_every_help": "Partial save frequency",
        "sidebar_about": "📋 About",
        "sidebar_software_name": "Transpetro Easy Route",
        "sidebar_version": "Version 3.0",
        "sidebar_inpi": "INPI: BR5120260XXXXX-X",
        "sidebar_authors_label": "👥 Authors",
        "sidebar_authors": [
          '<a href="https://www.linkedin.com/in/andersonportella" target="_blank">Anderson Portella</a> — UFF — andersonportella@yahoo.com.br',
          '<a href="https://www.linkedin.com/in/robsonsouza77/" target="_blank">Robson Ferreira de Souza</a> — IME — souzarbsn@gmail.com',
          '<a href="https://www.linkedin.com/in/profmarcosdossantos/" target="_blank">Prof. Dr. Marcos dos Santos</a> — Escola Naval — marcos.santos@marinha.mil.br',
          '<a href="https://www.linkedin.com/in/carlos-francisco-sim%C3%B5es-gomes-0906a944" target="_blank">Prof. Dr. Carlos Francisco Simões Gomes</a> — UFF — carlos_gomes@id.uff.br',
        ],
        "sidebar_links": "🔗 Links",
        "sidebar_manual": "📖 User Manual",
        "sidebar_citation": "📝 How to Cite",
        "sidebar_support": "🛠️ Support",
        "citation_title": "📝 Citation Formats",
        "citation_abnt": "ABNT",
        "citation_apa": "APA",
        "citation_software": "Software (INPI)",
        "mode_label": "Entry mode",
        "mode_base": "Use Transpetro Centers database",
        "mode_manual": "Enter manually",
        "mode_batch": "Batch processing (File upload)",
        "origin_label": "Origin",
        "dest_label": "Destination",
        "uo_label": "OU",
        "calc_button": "🚚 Calculate Route",
        "base_not_found": (
            "❌ Base files not found. Please check that "
            "'nomes e localização.csv' and 'coordenadas_consolidadas.csv' "
            "are in the app directory."
        ),
        "manual_origin": "Origin Name",
        "manual_lat_o": "Origin Latitude",
        "manual_lon_o": "Origin Longitude",
        "manual_dest": "Destination Name",
        "manual_lat_d": "Destination Latitude",
        "manual_lon_d": "Destination Longitude",
        "manual_coords_warning": "⚠️ Please enter origin and destination coordinates.",
        "batch_title": "📋 Batch Processing",
        "batch_download_template": "📥 Download Excel Template",
        "batch_step1": "**1. Download the template:**",
        "batch_step2": "**2. Fill in the template with your routes**",
        "batch_step2_caption": (
            "Required columns: Nome_Origem, Latitude_Origem, Longitude_Origem, "
            "Nome_Destino, Latitude_Destino, Longitude_Destino"
        ),
        "batch_step3": "**3. Upload the filled file:**",
        "batch_upload_label": "Choose Excel or CSV file",
        "batch_upload_help": "File must contain the template columns",
        "batch_loaded": "✅ File loaded! {} routes found.",
        "batch_view_data": "📊 View loaded data",
        "batch_missing_cols": "❌ Missing columns: {}",
        "batch_no_key": "⚠️ Please enter and validate your API key in the sidebar.",
        "batch_time_estimate": (
            "⏱️ Estimated time: ~{:.0f} min "
            "({} routes × {}s pause). "
            "Chunks of {} routes, saving every {}."
        ),
        "batch_calc_button": "🚚 Calculate All Routes",
        "batch_clear_partial": "🗑️ Clear partial ({} routes)",
        "batch_resuming": "♻️ Resuming from route {} ({} already processed).",
        "batch_done": "✅ Done! {} routes processed.",
        "batch_results_title": "📊 Results",
        "batch_stats_calc": "Calculated Routes",
        "batch_stats_same": "Origin = Destination",
        "batch_stats_err": "Errors",
        "batch_downloads": "📥 Downloads",
        "batch_dl_excel": "📊 Download Results (Excel)",
        "batch_dl_json": "📊 Download Results (JSON)",
        "batch_error": "❌ Error processing file: {}",
        "result_dist_km": "Distance (km)",
        "result_dist_mi": "Distance (mi)",
        "result_time": "Estimated time (min)",
        "result_calc_at": "Calculated at: {}",
        "result_success": "✅ Route calculated successfully!",
        "result_same_place": "✅ Origin and destination are the same location (≤ 10 m). No displacement.",
        "err_invalid_coords": "❌ Invalid coordinates (missing values).",
        "err_invalid_coords2": "❌ Invalid coordinates. Please check origin and destination data.",
        "err_no_key": "⚠️ Please enter and validate your API key in the sidebar.",
        "err_calc": "❌ Error calculating route: {}",
        "spinner_calc": "Calculating route...",
    },
}


def t(key: str) -> str:
    """Retorna a string traduzida para o idioma atual."""
    lang = st.session_state.get("lang", "pt")
    return TRANSLATIONS[lang].get(key, key)


# ================== FUNÇÕES UTILITÁRIAS ==================
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6_371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _parse_coords(value) -> float:
    return float(str(value).replace(",", "."))


# ================== VALIDAÇÃO DE CHAVES ==================
def validar_chave_ors(api_key: str) -> bool:
    """Faz uma requisição mínima para verificar se a chave ORS é válida."""
    try:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        body = {
            "coordinates": [[-43.1729, -22.9068], [-43.2096, -22.9035]],
            "instructions": False,
            "radiuses": [1000, 1000],
            "units": "km",
        }
        r = requests.post(url, json=body, headers=headers, timeout=10)
        if r.status_code == 200:
            return True
        if r.status_code in (401, 403):
            return False
        # Outros erros (429, 5xx) — chave pode ser válida, apenas com limite
        return r.status_code not in (401, 403)
    except Exception:
        return False


def validar_chave_google(api_key: str) -> bool:
    """Faz uma requisição mínima para verificar se a chave Google é válida."""
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": "-22.9068,-43.1729",
            "destinations": "-22.9035,-43.2096",
            "mode": "driving",
            "key": api_key,
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        status = data.get("status", "")
        return status in ("OK", "ZERO_RESULTS")
    except Exception:
        return False


# ================== CÁLCULO ORS ==================
def calcular_ors(lat_o, lon_o, lat_d, lon_d, api_key, snap=1000, max_retries=3):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Transpetro-RotaFacil/3.0",
    }
    body = {
        "coordinates": [[float(lon_o), float(lat_o)], [float(lon_d), float(lat_d)]],
        "instructions": False,
        "radiuses": [int(snap), int(snap)],
        "units": "km",
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=body, headers=headers, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 ** attempt)
                last_error = Exception(f"HTTP {r.status_code} na tentativa {attempt}/{max_retries}")
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                err = data["error"]
                msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                raise Exception(f"API error: {msg}")
            if "features" in data:
                summary = data["features"][0]["properties"]["summary"]
            elif "routes" in data:
                summary = data["routes"][0]["summary"]
            else:
                raise Exception(f"Unexpected response format. Keys: {list(data.keys())}")
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
            raise Exception(f"HTTP error: {error_msg}") from e
        except requests.ConnectionError as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise Exception(f"Connection failed after {max_retries} attempts") from e

    raise Exception(f"Failed after {max_retries} attempts: {last_error}")


# ================== CÁLCULO GOOGLE MAPS ==================
def calcular_google(lat_o, lon_o, lat_d, lon_d, api_key):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{lat_o},{lon_o}",
        "destinations": f"{lat_d},{lon_d}",
        "mode": "driving",
        "language": "pt-BR",
        "key": api_key,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    if data.get("status") != "OK":
        raise Exception(f"Google API status: {data.get('status')} — {data.get('error_message', '')}")

    element = data["rows"][0]["elements"][0]
    if element.get("status") != "OK":
        raise Exception(f"Route element status: {element.get('status')}")

    dist_km = round(element["distance"]["value"] / 1000, 3)
    dist_mi = round(dist_km * 0.621371, 3)
    tempo_min = round(element["duration"]["value"] / 60, 1)
    return dist_km, dist_mi, tempo_min


# ================== DISPATCHER ==================
def calcular_rota(lat_o, lon_o, lat_d, lon_d, api_key, engine, snap=1000):
    """Chama ORS ou Google dependendo do engine selecionado."""
    if engine == "ors":
        return calcular_ors(lat_o, lon_o, lat_d, lon_d, api_key, snap=snap)
    else:
        return calcular_google(lat_o, lon_o, lat_d, lon_d, api_key)


# ================== RESULTADO LINHA ==================
def _build_row(row, dist_km, dist_mi, tempo_min, status):
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


def processar_rota_individual(row, api_key, engine, snap):
    try:
        lat_o = _parse_coords(row["Latitude_Origem"])
        lon_o = _parse_coords(row["Longitude_Origem"])
        lat_d = _parse_coords(row["Latitude_Destino"])
        lon_d = _parse_coords(row["Longitude_Destino"])
    except (ValueError, TypeError) as e:
        return _build_row(row, None, None, None, f"Erro coordenadas: {e}")

    if haversine_km(lat_o, lon_o, lat_d, lon_d) < 0.01:
        return _build_row(row, 0, 0, 0, "Origem = Destino")

    try:
        dist_km, dist_mi, tempo_min = calcular_rota(lat_o, lon_o, lat_d, lon_d, api_key, engine, snap)
        return _build_row(row, dist_km, dist_mi, tempo_min, "Calculado")
    except Exception as e:
        return _build_row(row, None, None, None, f"Erro: {e}")


# ================== PROCESSAMENTO EM LOTE ==================
def processar_lote(df, api_key, engine, snap, chunk_size, sleep_base, save_every):
    total = len(df)
    n_chunks = math.ceil(total / chunk_size)

    if "resultados_parciais" not in st.session_state:
        st.session_state.resultados_parciais = []

    ja_processados = len(st.session_state.resultados_parciais)
    if ja_processados > 0:
        st.info(t("batch_resuming").format(ja_processados + 1, ja_processados))

    resultados = list(st.session_state.resultados_parciais)
    progress_bar = st.progress(ja_processados / total if total > 0 else 0)
    status_text = st.empty()
    stats_container = st.empty()

    for chunk_idx in range(n_chunks):
        inicio = chunk_idx * chunk_size
        fim = min(inicio + chunk_size, total)

        if fim <= ja_processados:
            continue

        start_row = max(inicio, ja_processados)
        status_text.text(
            f"📦 Bloco {chunk_idx + 1}/{n_chunks}  |  "
            f"Rotas {start_row + 1}–{fim} de {total}"
        )

        for idx in range(start_row, fim):
            row = df.iloc[idx]
            resultado = processar_rota_individual(row, api_key, engine, snap)
            resultados.append(resultado)

            processados = len(resultados)
            progress_bar.progress(processados / total)

            if processados % save_every == 0:
                st.session_state.resultados_parciais = list(resultados)
                stats_container.caption(f"💾 {processados}/{total} rotas")

            time.sleep(sleep_base)

    progress_bar.empty()
    status_text.empty()
    stats_container.empty()
    st.session_state.resultados_parciais = []

    return pd.DataFrame(resultados)


# ================== HELPERS ==================
def gerar_template():
    return pd.DataFrame({
        "Nome_Origem": ["Exemplo 1", "Exemplo 2"],
        "Latitude_Origem": [-22.9068, -23.5505],
        "Longitude_Origem": [-43.1729, -46.6333],
        "Nome_Destino": ["Exemplo Destino 1", "Exemplo Destino 2"],
        "Latitude_Destino": [-22.9035, -23.5489],
        "Longitude_Destino": [-43.2096, -46.6388],
    })


def resultado_para_excel(df_resultado):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Resultados")
    buffer.seek(0)
    return buffer


def exibir_resultado_individual(dist_km, dist_mi, tempo_min, units_opt):
    cols = st.columns(3)
    if units_opt == "mi":
        cols[0].metric(t("result_dist_mi"), dist_mi)
        cols[1].metric(t("result_dist_km"), dist_km)
    else:
        cols[0].metric(t("result_dist_km"), dist_km)
        cols[1].metric(t("result_dist_mi"), dist_mi)
    cols[2].metric(t("result_time"), tempo_min)
    st.caption(t("result_calc_at").format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


def calcular_rota_individual_ui(lat_o, lon_o, lat_d, lon_d, api_key, engine, snap_radius, units_opt):
    try:
        lat_o_f, lon_o_f = float(lat_o), float(lon_o)
        lat_d_f, lon_d_f = float(lat_d), float(lon_d)
        if any(math.isnan(v) for v in [lat_o_f, lon_o_f, lat_d_f, lon_d_f]):
            st.error(t("err_invalid_coords"))
            return
    except (ValueError, TypeError):
        st.error(t("err_invalid_coords2"))
        return

    if haversine_km(lat_o_f, lon_o_f, lat_d_f, lon_d_f) < 0.01:
        st.info(t("result_same_place"))
        return

    if not api_key:
        st.error(t("err_no_key"))
        return

    with st.spinner(t("spinner_calc")):
        try:
            dist_km, dist_mi, tempo_min = calcular_rota(
                lat_o_f, lon_o_f, lat_d_f, lon_d_f, api_key, engine, snap=snap_radius
            )
            st.success(t("result_success"))
            exibir_resultado_individual(dist_km, dist_mi, tempo_min, units_opt)
        except Exception as e:
            st.error(t("err_calc").format(e))


# ================== CARGA DA BASE TRANSPETRO ==================
@st.cache_data
def carregar_base():
    centros = None
    coords = None
    for enc in ("utf-8", "latin-1", "ISO-8859-1"):
        try:
            centros = pd.read_csv("nomes e localização.csv", sep=";", encoding=enc)
            break
        except (UnicodeDecodeError, FileNotFoundError):
            pass

    for enc in ("utf-8", "latin-1", "ISO-8859-1"):
        try:
            coords = pd.read_csv("coordenadas_consolidadas.csv", encoding=enc)
            break
        except (UnicodeDecodeError, FileNotFoundError):
            pass

    if centros is None or coords is None:
        return None, {}

    base = centros.merge(coords, on="Centro", how="left")
    base["label"] = (
        base["Centro"] + " – " + base["Denominação"] + " (" + base["Local"] + ")"
    )
    label_map = {row["label"]: row for _, row in base.iterrows()}
    return base, label_map


base, label_to_row = carregar_base()


# ================== SIDEBAR ==================
with st.sidebar:
    try:
        mascote = Image.open("Mascote.png")
        st.sidebar.image(mascote, width=150)
    except Exception:
        pass

    # --- Idioma ---
    lang_choice = st.selectbox(
        "🌐 Idioma / Language",
        options=["Português", "English"],
        index=0 if st.session_state.get("lang", "pt") == "pt" else 1,
        key="lang_selector",
    )
    st.session_state["lang"] = "pt" if lang_choice == "Português" else "en"

    st.divider()

    # --- Configurações ---
    st.header(t("sidebar_settings"))

    # Motor de API (toggle)
    engine_choice = st.radio(
        t("sidebar_api_engine"),
        options=[t("sidebar_ors_label"), t("sidebar_google_label")],
        index=0,
        help=t("sidebar_api_tip"),
        key="engine_radio",
    )
    engine = "ors" if engine_choice == t("sidebar_ors_label") else "google"

    st.info(t("sidebar_api_tip"))

    # Chave de API com validação automática
    if engine == "ors":
        api_key = st.text_input(
            t("sidebar_api_key_ors"),
            type="password",
            help=t("sidebar_api_key_help_ors"),
            key="api_key_ors",
        )
        chave_valida = False
        if api_key:
            with st.spinner(t("sidebar_api_validating")):
                chave_valida = validar_chave_ors(api_key)
            if chave_valida:
                st.success(t("sidebar_api_valid_ors"))
            else:
                st.error(t("sidebar_api_invalid"))
    else:
        api_key = st.text_input(
            t("sidebar_api_key_google"),
            type="password",
            help=t("sidebar_api_key_help_google"),
            key="api_key_google",
        )
        chave_valida = False
        if api_key:
            with st.spinner(t("sidebar_api_validating")):
                chave_valida = validar_chave_google(api_key)
            if chave_valida:
                st.success(t("sidebar_api_valid_google"))
            else:
                st.error(t("sidebar_api_invalid"))

    # Parâmetros gerais
    snap_radius = st.number_input(
        t("sidebar_snap"),
        min_value=50, max_value=5000, value=1000, step=50,
        help=t("sidebar_snap_help"),
        disabled=(engine == "google"),
    )
    units_opt = st.selectbox(t("sidebar_units"), ["km", "mi"], index=0)

    # Parâmetros de lote
    st.divider()
    st.subheader(t("sidebar_batch_params"))
    CHUNK_SIZE = st.number_input(
        t("sidebar_chunk"), min_value=50, max_value=1000, value=500, step=50,
        help=t("sidebar_chunk_help"),
    )
    SLEEP_BASE = st.slider(
        t("sidebar_sleep"), min_value=0.1, max_value=2.0, value=0.3, step=0.1,
        help=t("sidebar_sleep_help"),
    )
    SAVE_EVERY = st.number_input(
        t("sidebar_save_every"), min_value=10, max_value=500, value=50, step=10,
        help=t("sidebar_save_every_help"),
    )

    st.divider()

    # --- Sobre o Software ---
    st.header(t("sidebar_about"))
    st.markdown(f"**{t('sidebar_software_name')}**  \n{t('sidebar_version')}")
    st.caption(t("sidebar_inpi"))

    st.markdown(f"**{t('sidebar_authors_label')}**")
    st.markdown("<br>".join(t("sidebar_authors")), unsafe_allow_html=True)

    st.divider()

    # --- Links ---
    st.markdown(f"**{t('sidebar_links')}**")

    # Manual
    st.markdown(
        f"[{t('sidebar_manual')}](https://github.com/andersonportella-collab/Transpetro-Rota-Facil/blob/main/Manual_Transpetro_Rota_Facil_v3.pdf)"
    )

    # Citações (expander)
    with st.expander(t("sidebar_citation")):
        lang = st.session_state.get("lang", "pt")
        autores = "PORTELLA, A.; SOUZA, R.; DOS SANTOS, M.; SIMÕES, C."
        ano = datetime.now().year

        tab_abnt, tab_apa, tab_sw = st.tabs([
            t("citation_abnt"), t("citation_apa"), t("citation_software")
        ])

        with tab_abnt:
            st.code(
                f"{autores} "
                f"Transpetro Rota Fácil: simulador de distância e tempo rodoviário. "
                f"Rio de Janeiro: INPI, {ano}. "
                f"Registro de Programa de Computador nº BR5120260XXXXX-X.",
                language="text",
            )

        with tab_apa:
            st.code(
                f"Portella, A., Souza, R., dos Santos, M., & Simões, C. ({ano}). "
                f"Transpetro Rota Fácil [Computer software]. "
                f"Instituto Nacional da Propriedade Industrial. "
                f"BR5120260XXXXX-X.",
                language="text",
            )

        with tab_sw:
            st.code(
                f"Nome: Transpetro Rota Fácil\n"
                f"Autores: Anderson Portella, Robson Souza, Marcos dos Santos, Carlos Simões\n"
                f"Registro INPI: BR5120260XXXXX-X\n"
                f"Ano: {ano}\n"
                f"Linguagem: Python / Streamlit\n"
                f"Engines: OpenRouteService, Google Maps Distance Matrix API",
                language="text",
            )

    # Suporte
    st.markdown(
        f"[{t('sidebar_support')}](mailto:suporte@transpetro.com.br)"
    )


# ================== TÍTULO PRINCIPAL ==================
st.title(t("app_title"))
st.caption(t("app_caption"))

# ================== MODO DE ENTRADA ==================
modo = st.radio(
    t("mode_label"),
    [t("mode_base"), t("mode_manual"), t("mode_batch")],
    horizontal=True,
)
st.divider()

# ================== PROCESSAMENTO EM LOTE ==================
if modo == t("mode_batch"):
    st.subheader(t("batch_title"))

    col1, col2 = st.columns([1, 2])
    with col1:
        st.write(t("batch_step1"))
        template = gerar_template()
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            template.to_excel(writer, index=False, sheet_name="Template")
        buffer.seek(0)
        st.download_button(
            label=t("batch_download_template"),
            data=buffer,
            file_name="template_rotas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col2:
        st.write(t("batch_step2"))
        st.caption(t("batch_step2_caption"))

    st.write(t("batch_step3"))
    uploaded_file = st.file_uploader(
        t("batch_upload_label"),
        type=["xlsx", "xls", "csv"],
        help=t("batch_upload_help"),
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)

            st.success(t("batch_loaded").format(len(df_upload)))

            with st.expander(t("batch_view_data")):
                st.dataframe(df_upload)

            colunas_obrigatorias = [
                "Nome_Origem", "Latitude_Origem", "Longitude_Origem",
                "Nome_Destino", "Latitude_Destino", "Longitude_Destino",
            ]
            colunas_faltantes = [c for c in colunas_obrigatorias if c not in df_upload.columns]

            if colunas_faltantes:
                st.error(t("batch_missing_cols").format(", ".join(colunas_faltantes)))
            elif not api_key or not chave_valida:
                st.warning(t("batch_no_key"))
            else:
                est_min = len(df_upload) * SLEEP_BASE / 60
                st.info(t("batch_time_estimate").format(
                    est_min, len(df_upload), SLEEP_BASE, CHUNK_SIZE, SAVE_EVERY
                ))

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    btn_calcular = st.button(t("batch_calc_button"), type="primary")
                with col_btn2:
                    if (
                        "resultados_parciais" in st.session_state
                        and len(st.session_state.resultados_parciais) > 0
                    ):
                        n_parciais = len(st.session_state.resultados_parciais)
                        btn_limpar = st.button(t("batch_clear_partial").format(n_parciais))
                        if btn_limpar:
                            st.session_state.resultados_parciais = []
                            st.rerun()

                if btn_calcular:
                    df_resultados = processar_lote(
                        df_upload, api_key, engine, snap_radius,
                        CHUNK_SIZE, SLEEP_BASE, SAVE_EVERY,
                    )
                    st.success(t("batch_done").format(len(df_resultados)))
                    st.subheader(t("batch_results_title"))
                    st.dataframe(df_resultados)

                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        t("batch_stats_calc"),
                        len(df_resultados[df_resultados["Status"] == "Calculado"]),
                    )
                    col2.metric(
                        t("batch_stats_same"),
                        len(df_resultados[df_resultados["Status"] == "Origem = Destino"]),
                    )
                    col3.metric(
                        t("batch_stats_err"),
                        len(df_resultados[df_resultados["Status"].str.contains("Erro", na=False)]),
                    )

                    st.subheader(t("batch_downloads"))
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label=t("batch_dl_excel"),
                            data=resultado_para_excel(df_resultados),
                            file_name=f"resultados_rotas_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    with col_dl2:
                        st.download_button(
                            label=t("batch_dl_json"),
                            data=df_resultados.to_json(orient="records", date_format="iso"),
                            file_name=f"resultados_rotas_{datetime.now():%Y%m%d_%H%M%S}.json",
                            mime="application/json",
                        )

        except Exception as e:
            st.error(t("batch_error").format(e))

# ================== BASE TRANSPETRO ==================
elif modo == t("mode_base"):
    if base is None:
        st.error(t("base_not_found"))
    else:
        col1, col2 = st.columns(2)
        with col1:
            origem_label = st.selectbox(t("origin_label"), sorted(label_to_row.keys()))
            origem = label_to_row[origem_label]
            st.caption(f"{t('uo_label')}: {origem.get('UO', 'N/A')}")
        with col2:
            destino_label = st.selectbox(t("dest_label"), sorted(label_to_row.keys()))
            destino = label_to_row[destino_label]
            st.caption(f"{t('uo_label')}: {destino.get('UO', 'N/A')}")

        st.divider()
        if st.button(t("calc_button")):
            calcular_rota_individual_ui(
                origem["Latitude"], origem["Longitude"],
                destino["Latitude"], destino["Longitude"],
                api_key, engine, snap_radius, units_opt,
            )

# ================== MODO MANUAL ==================
else:
    col1, col2 = st.columns(2)
    with col1:
        nome_o = st.text_input(t("manual_origin"))
        lat_o = st.number_input(t("manual_lat_o"), format="%.8f")
        lon_o = st.number_input(t("manual_lon_o"), format="%.8f")
    with col2:
        nome_d = st.text_input(t("manual_dest"))
        lat_d = st.number_input(t("manual_lat_d"), format="%.8f")
        lon_d = st.number_input(t("manual_lon_d"), format="%.8f")

    st.divider()
    if st.button(t("calc_button")):
        if lat_o == 0 and lon_o == 0 and lat_d == 0 and lon_d == 0:
            st.warning(t("manual_coords_warning"))
        else:
            calcular_rota_individual_ui(
                lat_o, lon_o, lat_d, lon_d,
                api_key, engine, snap_radius, units_opt,
            )
