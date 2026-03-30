# 🚚 Transpetro Rota Fácil

Simulador de tempo e distância rodoviária entre unidades operacionais, com suporte a dois motores de cálculo: [OpenRouteService](https://openrouteservice.org/) (gratuito) e [Google Maps Distance Matrix API](https://developers.google.com/maps/documentation/distance-matrix).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-3.0-orange)

---

## Funcionalidades

- **Dois motores de API**: OpenRouteService (gratuito) ou Google Maps (maior volume)
- **Interface bilíngue** (Português / English), alternável em tempo real
- **Validação automática de chave** de API antes do processamento
- **Rota individual** a partir de base pré-cadastrada ou coordenadas manuais
- **Processamento em lote** de milhares de rotas via upload de planilha (Excel/CSV)
- **Robustez para grandes volumes**: chunking, rate limit com backoff exponencial e persistência parcial
- Exportação de resultados em **Excel** e **JSON** (compatível com Power BI)
- Detecção automática de pares origem = destino
- Suporte a coordenadas com vírgula decimal (padrão brasileiro)
- Seção **Como Citar** integrada (ABNT, APA, Software/INPI)

## Arquitetura

```
┌──────────────────────────────────────────────────────┐
│                    Streamlit UI                       │
│          (Bilíngue: pt-BR / en)                      │
│  ┌───────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │Base Centros│  │  Manual  │  │  Upload em Lote   │  │
│  └─────┬─────┘  └────┬─────┘  └────────┬──────────┘  │
│        └──────────────┼─────────────────┘             │
│                       ▼                               │
│              calcular_rota()                          │
│              (dispatcher)                             │
│            ┌─────┴──────┐                             │
│            ▼            ▼                             │
│     calcular_ors()  calcular_google()                 │
│     retry+backoff   Distance Matrix                   │
│            │            │                             │
│            ▼            ▼                             │
│    OpenRouteService   Google Maps                     │
│    Directions v2      Distance Matrix API             │
└──────────────────────────────────────────────────────┘
```

## Pré-requisitos

- Python 3.10+
- Chave de API de pelo menos um dos motores:
  - **OpenRouteService** (gratuito): [openrouteservice.org/dev/#/signup](https://openrouteservice.org/dev/#/signup)
  - **Google Maps** (pago com crédito mensal gratuito): [Google Cloud Console](https://console.cloud.google.com/)

### Comparação dos motores

| Critério | OpenRouteService | Google Maps |
|----------|-----------------|-------------|
| Custo | Gratuito (sem cartão) | Pago (US$ 200/mês de crédito gratuito) |
| Limite diário | 2.000 req/dia | Baseado em crédito |
| Rate limit | 40 req/min | Mais permissivo |
| Ideal para | Até ~500 rotas/dia | Grandes volumes (> 500 rotas) |
| Snapping radius | Configurável | Não aplicável |

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/Anderson-Portella/Rota-Facil-TP.git
cd Rota-Facil-TP

# Criar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Configuração

### 1. Chave da API

A chave é informada diretamente na barra lateral do aplicativo (campo com máscara de senha). O app valida automaticamente a chave antes de permitir o cálculo.

**OpenRouteService (gratuito):**
1. Acesse [openrouteservice.org/dev/#/signup](https://openrouteservice.org/dev/#/signup)
2. Crie uma conta (não exige cartão de crédito)
3. Gere um token no painel de desenvolvedor
4. Cole o token no campo "Chave da API — OpenRouteService"

**Google Maps:**
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Ative a Distance Matrix API
3. Gere uma chave de API
4. Cole no campo "Chave da API — Google Maps"

### 2. Bases de dados (opcional)

Para o modo "Base de Centros", coloque na raiz do projeto:

- `nomes e localização.csv` — cadastro de centros (separador `;`)
- `coordenadas_consolidadas.csv` — coordenadas geográficas

Ambos devem compartilhar a coluna `Centro` como chave de junção.

### 3. Mascote (opcional)

Coloque uma imagem `Mascote.png` na raiz do projeto para exibir na barra lateral.

## Uso

```bash
streamlit run app.py
```

### Modo 1: Base de Centros

Selecione origem e destino nos dropdowns e clique em **Calcular Rota**.

### Modo 2: Manual

Informe nome e coordenadas (latitude/longitude) de origem e destino.

### Modo 3: Processamento em Lote

1. Baixe o template Excel pelo botão na interface
2. Preencha com suas rotas (colunas obrigatórias abaixo)
3. Ajuste a pausa entre chamadas (1.6s para ORS gratuito)
4. Faça upload e clique em **Calcular Todas as Rotas**

#### Colunas obrigatórias do template

| Coluna | Tipo | Exemplo |
|--------|------|---------|
| `Nome_Origem` | texto | Terminal Duque de Caxias |
| `Latitude_Origem` | float | -22.4716 |
| `Longitude_Origem` | float | -43.3019 |
| `Nome_Destino` | texto | Terminal de Ilha d'Água |
| `Latitude_Destino` | float | -22.8584 |
| `Longitude_Destino` | float | -43.1365 |

### Parâmetros de lote recomendados

| Parâmetro | Default | Recomendado (ORS gratuito) | Descrição |
|-----------|---------|----------------------------|-----------|
| Tamanho do bloco | 500 | 500 | Rotas por chunk |
| Pausa entre chamadas | 0.3 s | **1.6 s** | Respeita 40 req/min |
| Salvar parcial a cada | 50 | 50 | Frequência de checkpoint |

## Estrutura do Projeto

```
Rota-Facil-TP/
├── app.py                          # Aplicação principal (v3.0)
├── requirements.txt                # Dependências Python
├── README.md                       # Este arquivo
├── LICENSE                         # Licença MIT
├── CHANGELOG.md                    # Histórico de versões
├── CONTRIBUTING.md                 # Guia de contribuição
├── .gitignore                      # Arquivos ignorados pelo git
├── .streamlit/
│   └── config.toml                 # Configurações do Streamlit
├── Mascote.png                     # (opcional) Imagem da sidebar
├── nomes e localização.csv         # (opcional) Base de centros
└── coordenadas_consolidadas.csv    # (opcional) Coordenadas
```

## Mecanismos de Robustez

### 1. Chunking
O DataFrame é dividido em blocos configuráveis, com progresso visual por bloco.

### 2. Rate Limit com Backoff Exponencial
Pausa configurável entre chamadas. Em caso de HTTP 429 ou erros 5xx, até 3 retentativas com espera exponencial (2s, 4s, 8s).

### 3. Persistência Parcial
Resultados salvos periodicamente em `st.session_state`. Retomada automática dentro da mesma sessão do navegador.

## Autores

| Autor | Instituição | Contato |
|-------|-------------|---------|
| [Anderson Portella](https://www.linkedin.com/in/andersonportella) | Universidade Federal Fluminense (UFF) | andersonportella@yahoo.com.br |
| [Robson Ferreira de Souza](https://www.linkedin.com/in/robsonsouza77/) | Instituto Militar de Engenharia (IME) | souzarbsn@gmail.com |
| [Prof. Dr. Marcos dos Santos](https://www.linkedin.com/in/intfranciscomarcos) | Escola Naval | marcos.santos@marinha.mil.br |
| [Prof. Dr. Carlos Francisco Simões Gomes](https://www.linkedin.com/in/carlos-francisco-sim%C3%B5es-gomes-0906a944) | Universidade Federal Fluminense (UFF) | carlos_gomes@id.uff.br |

## Como Citar

### ABNT
```
PORTELLA, A.; SOUZA, R.; DOS SANTOS, M.; SIMÕES, C. Transpetro Rota Fácil:
simulador de distância e tempo rodoviário. Rio de Janeiro: INPI, 2026.
Registro de Programa de Computador nº BR5120260XXXXX-X.
```

### APA
```
Portella, A., Souza, R., dos Santos, M., & Simões, C. (2026).
Transpetro Rota Fácil [Computer software].
Instituto Nacional da Propriedade Industrial. BR5120260XXXXX-X.
```

## Contribuição

Veja o arquivo [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

## Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## Créditos

- [OpenRouteService](https://openrouteservice.org/) — API de rotas (Heidelberg Institute for Geoinformation Technology)
- [Google Maps Platform](https://developers.google.com/maps) — Distance Matrix API
- [Streamlit](https://streamlit.io/) — Framework de interface
