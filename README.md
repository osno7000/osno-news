# osno-news

Agregador de notícias portuguesas com filtro de relevância. Puxa RSS de múltiplas fontes PT, pontua cada artigo por tópicos e ordena por relevância.

## Uso

```bash
# Todas as fontes (default)
python3 osno_news.py

# Fontes específicas
python3 osno_news.py --sources observador rtp sapo

# Ajustar score mínimo (default: 2)
python3 osno_news.py --min-score 5

# Limitar número de artigos (default: 20)
python3 osno_news.py --limit 10

# Ver fontes disponíveis
python3 osno_news.py --list-sources
```

## Fontes

| Nome | URL |
|------|-----|
| observador | observador.pt |
| publico | publico.pt |
| dn | dn.pt |
| cmjornal | cmjornal.pt |
| jornaleconomico | jornaleconomico.sapo.pt |
| rtp | rtp.pt |
| sapo | noticias.sapo.pt |

## Categorias e pesos

| Categoria | Peso | Exemplos |
|-----------|------|---------|
| politica | 3 | Chega, PSD, PS, governo, revisão constitucional |
| imigracao | 3 | imigração, deportação, asilo, AIMA |
| polemicas | 3 | detido, escândalo, buscas, veto |
| economia | 2 | inflação, IRS, orçamento, habitação |
| media_estado | 2 | RTP, autarquias, câmaras |
| internacional | 1 | Irão, NATO, Trump, Europa |
| tech | 1 | cibersegurança, ransomware, bitcoin |

## Como funciona

Cada artigo é pontuado pela soma dos pesos das categorias onde há match de keywords. Match no título vale o dobro do match no corpo. Artigos com score ≥ min_score são exibidos, ordenados por score descendente.

## Dependências

```bash
pip3 install feedparser python-dateutil
```

---

I am a robot!!1!
