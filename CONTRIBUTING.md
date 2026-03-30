# Guia de Contribuição

Obrigado pelo interesse em contribuir com o **Transpetro Rota Fácil**!

## Como contribuir

### Reportar bugs

Abra uma [Issue](../../issues) com:
- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs. observado
- Motor de API utilizado (ORS ou Google)
- Idioma selecionado (pt / en)
- Screenshots (se aplicável)
- Versão do Python e do Streamlit

### Sugerir melhorias

Abra uma Issue com a tag `enhancement` descrevendo:
- O problema que a melhoria resolve
- Proposta de solução
- Alternativas consideradas

### Enviar código

1. Faça um fork do repositório
2. Crie uma branch descritiva:
   ```bash
   git checkout -b feature/descricao-curta
   # ou
   git checkout -b fix/descricao-do-bug
   ```
3. Faça suas alterações seguindo as convenções abaixo
4. Teste localmente com `streamlit run app.py`
5. Verifique os dois idiomas (pt e en) e ambos os motores (ORS e Google)
6. Commit com mensagens no padrão [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: adiciona exportação em CSV"
   git commit -m "fix: corrige parsing de coordenadas negativas"
   ```
7. Push e abra um Pull Request

## Convenções de código

- **Python**: PEP 8, type hints quando possível
- **Docstrings**: formato Google
- **Internacionalização**: toda string visível ao usuário deve estar no dicionário `TRANSLATIONS` (pt e en)
- **Idioma do código**: variáveis e funções em inglês ou português (manter consistência com o existente)
- **Idioma da UI**: bilíngue via sistema `t()`
- **Commits**: Conventional Commits em português ou inglês

## Ambiente de desenvolvimento

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
