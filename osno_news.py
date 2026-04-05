#!/usr/bin/env python3
"""
osno-news: agregador de notícias PT com filtro por relevância
Puxa RSS feeds, filtra por keywords, ordena por relevância
"""

import feedparser
import json
import sys
import argparse
from datetime import datetime, timezone
from dateutil import parser as dateparser

# RSS feeds PT
FEEDS = {
    "observador":    "https://observador.pt/feed/",
    "publico":       "http://feeds.feedburner.com/PublicoRSS",
    "dn":            "https://dn.pt/feed/",
    "cmjornal":      "https://www.cmjornal.pt/rss",
    "jornaleconomico": "https://jornaleconomico.sapo.pt/feed",
    "rtp":           "https://www.rtp.pt/noticias/rss",
    "sapo":          "https://noticias.sapo.pt/rss/",
    # Tech EN
    "hackernews":    "https://news.ycombinator.com/rss",
}

# Keywords por categoria com peso
KEYWORDS = {
    # Política — alta prioridade
    "politica": {
        "keywords": [
            "chega", "ventura", "psd", "ps", "cds", "il", "bloco", "pcp",
            "governo", "montenegro", "seguro", "parlamento", "ar", "constituição",
            "revisão constitucional", "lei da nacionalidade", "tc", "tribunal constitucional",
            "oposição", "maioria", "eleições", "coabitação",
        ],
        "weight": 3,
    },
    # Economia
    "economia": {
        "keywords": [
            "inflação", "défice", "orçamento", "pib", "desemprego", "salário",
            "fundos europeus", "prr", "combustíveis", "gasolina", "gasóleo",
            "bancos", "impostos", "irs", "irc", "habitação", "renda", "imóveis",
        ],
        "weight": 2,
    },
    # Imigração (hot topic)
    "imigracao": {
        "keywords": [
            "imigrantes", "imigração", "fronteiras", "deportação", "asilo",
            "refugiados", "cidadania", "naturalização", "sei", "aima",
        ],
        "weight": 3,
    },
    # Media e Estado
    "media_estado": {
        "keywords": [
            "rtp", "rádio", "televisão", "media pública", "subsídios",
            "câmara", "autarquias", "município", "câmaras",
        ],
        "weight": 2,
    },
    # Internacional relevante para PT
    "internacional": {
        "keywords": [
            "irão", "iran", "guerra", "nato", "trump", "europa", "ue",
            "rússia", "ucrânia", "israel", "energia", "petróleo",
            "macron", "merz", "scholz", "bruxelas",
            "lajes", "açores", "ormuz", "hormuz", "houthis",
            "estreito", "refinaria", "kuwait", "mq-9", "reaper",
        ],
        "weight": 1,
    },
    # Tech (keywords muito específicos para evitar falsos positivos)
    "tech": {
        "keywords": [
            "inteligência artificial", "cibersegurança", "hack", "ransomware",
            "startup", "bitcoin", "crypto", "blockchain", "github",
            # EN tech keywords for HackerNews
            "ai", "llm", "openai", "anthropic", "google", "apple", "nvidia",
            "kubernetes", "linux", "python", "rust", "golang",
            "funding", "ipo", "layoffs", "acquisition",
            "gpu", "inference", "model", "agent", "coding",
        ],
        "weight": 1,
    },
    # Finanças EN (para HN)
    "financas_en": {
        "keywords": [
            "recession", "inflation", "interest rate", "fed", "central bank",
            "stock market", "s&p", "nasdaq", "bond yield", "tariffs",
            "gdp", "unemployment", "earnings", "revenue", "profit",
        ],
        "weight": 2,
    },
    # Polémicas / viral (só termos de alto impacto)
    "polemicas": {
        "keywords": [
            "polémico", "escândalo", "corrupção", "buscas",
            "detido", "preso", "acusado", "condenado",
            "demissão", "demite", "chumbo", "veto",
        ],
        "weight": 3,
    },
}

def score_article(title: str, summary: str) -> tuple[int, list[str]]:
    """Score article relevance. Returns (score, matched_categories)"""
    text = (title + " " + summary).lower()
    total_score = 0
    matched = []

    for category, data in KEYWORDS.items():
        for kw in data["keywords"]:
            if kw in text:
                total_score += data["weight"]
                if category not in matched:
                    matched.append(category)
                break  # one match per category is enough for counting

    # Bonus: title match is worth more than summary match
    title_lower = title.lower()
    for category, data in KEYWORDS.items():
        for kw in data["keywords"]:
            if kw in title_lower:
                total_score += data["weight"]  # double weight for title
                break

    return total_score, matched


def fetch_feed(source: str, url: str, limit: int = 20) -> list[dict]:
    """Fetch and parse a single RSS feed."""
    try:
        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:limit]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "").strip()
            link = entry.get("link", "")

            # Parse date
            pub_date = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    pub_date = dt.strftime("%H:%M")
                except Exception:
                    pub_date = ""

            score, categories = score_article(title, summary)

            if score > 0:
                articles.append({
                    "source": source,
                    "title": title,
                    "summary": summary[:200] if summary else "",
                    "link": link,
                    "date": pub_date,
                    "score": score,
                    "categories": categories,
                })

        return articles

    except Exception as e:
        print(f"  [erro {source}]: {e}", file=sys.stderr)
        return []


def run(sources: list[str] | None = None, min_score: int = 2, limit: int = 20, show_all: bool = False, save: bool = False):
    """Main function — fetch feeds and display results."""
    import os

    feeds_to_check = {k: v for k, v in FEEDS.items() if sources is None or k in sources}

    print(f"\n📰 osno-news — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"   a puxar {len(feeds_to_check)} fontes...\n")

    all_articles = []
    for source, url in feeds_to_check.items():
        articles = fetch_feed(source, url)
        all_articles.extend(articles)
        print(f"  ✓ {source}: {len(articles)} artigos relevantes")

    # Sort by score descending
    all_articles.sort(key=lambda x: x["score"], reverse=True)

    # Filter by min_score
    if not show_all:
        all_articles = [a for a in all_articles if a["score"] >= min_score]

    print(f"\n{'─'*70}")
    print(f"  {len(all_articles)} artigos relevantes (score ≥ {min_score})")
    print(f"{'─'*70}\n")

    for i, art in enumerate(all_articles[:limit]):
        import re
        cats = ", ".join(art["categories"])
        date_str = f" {art['date']}" if art["date"] else ""
        # Clean title of CDATA artifacts
        title = re.sub(r'<!\[CDATA\[|\]\]>', '', art["title"]).strip()
        print(f"[{i+1:02d}] {art['source']}{date_str} | score={art['score']} | {cats}")
        print(f"     {title}")
        if art["summary"]:
            # Clean HTML from summary
            clean = re.sub(r'<[^>]+>', '', art["summary"])
            clean = re.sub(r'\s+', ' ', clean).strip()[:160]
            if clean:
                print(f"     → {clean}")
        print(f"     {art['link']}")
        print()

    if not all_articles:
        print("  (sem artigos relevantes encontrados)")

    if save:
        save_dir = os.path.expanduser("~/mind/news")
        os.makedirs(save_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        save_path = os.path.join(save_dir, f"{date_str}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump({
                "date": datetime.now().isoformat(),
                "count": len(all_articles),
                "articles": all_articles[:limit]
            }, f, ensure_ascii=False, indent=2)
        print(f"\n  💾 guardado em {save_path} ({len(all_articles[:limit])} artigos)")


def main():
    parser = argparse.ArgumentParser(description="osno-news: agregador de notícias PT")
    parser.add_argument("--sources", "-s", nargs="+", choices=list(FEEDS.keys()),
                        help="fontes específicas (default: todas)")
    parser.add_argument("--min-score", "-m", type=int, default=2,
                        help="score mínimo (default: 2)")
    parser.add_argument("--limit", "-l", type=int, default=20,
                        help="número máximo de artigos (default: 20)")
    parser.add_argument("--list-sources", action="store_true",
                        help="listar fontes disponíveis")
    parser.add_argument("--json", action="store_true",
                        help="output em JSON")
    parser.add_argument("--save", action="store_true",
                        help="guardar artigos em ~/mind/news/YYYY-MM-DD.json")

    args = parser.parse_args()

    if args.list_sources:
        print("\nFontes disponíveis:")
        for name, url in FEEDS.items():
            print(f"  {name:20} {url}")
        return

    run(
        sources=args.sources,
        min_score=args.min_score,
        limit=args.limit,
        save=args.save,
    )


if __name__ == "__main__":
    main()
