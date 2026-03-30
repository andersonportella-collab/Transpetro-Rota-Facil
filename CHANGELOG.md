# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [3.0.0] - 2026-03-30

### Adicionado
- **Dual engine**: suporte a OpenRouteService (ORS) e Google Maps Distance Matrix API, selecionável via radio button na sidebar
- **Interface bilíngue** (Português / English) com alternância em tempo real via dropdown
- **Validação automática de chave** de API (requisição de teste ao selecionar motor e informar chave)
- Dispatcher `calcular_rota()` que roteia para ORS ou Google conforme seleção do usuário
- Função `calcular_google()` para integração com Google Distance Matrix API
- Funções `validar_chave_ors()` e `validar_chave_google()` com requisição mínima de teste
- Dica de volume na sidebar recomendando Google para lotes > 500 rotas
- Raio de snapping desabilitado automaticamente quando Google está selecionado
- Seção **Sobre o Software** na sidebar com versão, INPI, autores com links LinkedIn e afiliações
- Seção **Como Citar** com abas ABNT, APA e Software/INPI
- Link de suporte por e-mail na sidebar
- Seletor de modo de entrada com layout horizontal (`horizontal=True`)
- Sistema completo de internacionalização (`TRANSLATIONS` dict + função `t()`)

### Alterado
- User-Agent atualizado para `Transpetro-RotaFacil/3.0`
- Pausa padrão entre chamadas reduzida para 0.3s (ajustável pelo usuário)
- Validação de chave agora é pré-requisito para habilitar botão de cálculo em lote

## [2.0.0] - 2026-03-26

### Adicionado
- Chunking real no processamento em lote (divisão em blocos configuráveis)
- Retry com backoff exponencial para HTTP 429 e erros 5xx (até 3 tentativas)
- Persistência parcial de resultados via `session_state` com retomada automática
- Parâmetros de lote configuráveis na sidebar (chunk size, pausa, frequência de salvamento)
- Estimativa de tempo exibida antes do processamento
- Botão para limpar resultados parciais
- Função `carregar_base()` com `@st.cache_data`
- Validação e fallback quando arquivos de base não existem
- Suporte a coordenadas com vírgula decimal (padrão brasileiro)

### Corrigido
- Chamada solta `calcular_ors(...)` sem argumentos na função `processar_lote`
- `resultados.append()` duplicado causando registros repetidos
- `time.sleep()` posicionado fora do fluxo correto
- Tratamento de erro inconsistente entre os três modos de entrada

### Alterado
- Refatoração completa: funções extraídas e desacopladas
- Eliminação de código duplicado entre os modos de entrada

## [1.0.0] - 2026-03-26

### Adicionado
- Versão inicial do aplicativo Streamlit
- Três modos de entrada: base de centros, manual e upload em lote
- Integração com API OpenRouteService (Directions v2, driving-car)
- Cálculo de distância (km/mi) e tempo estimado
- Download de resultados em Excel e JSON
- Fórmula de Haversine para detecção de origem = destino
- Template Excel para processamento em lote
