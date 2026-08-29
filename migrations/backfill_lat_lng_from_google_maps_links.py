# -*- coding: utf-8 -*-
"""
Backfill: preenche latitude/longitude de prédios e unidades a partir do link do Google Maps.

Motivação:
  - Evitar geocoding online (lento e pode errar cidade).
  - Usar coordenadas reais já presentes na URL final do Maps.

Uso (PowerShell):
  python migrations/backfill_lat_lng_from_google_maps_links.py --dry-run
  python migrations/backfill_lat_lng_from_google_maps_links.py
  python migrations/backfill_lat_lng_from_google_maps_links.py --limit 50

Observações:
  - Para links curtos (maps.app.goo.gl), o script faz uma requisição HTTP para seguir o redirect
    e obter a URL final (onde normalmente existe @lat,lng ou !3d/!4d).
  - Se uma unidade tiver predio_id e NÃO tiver coordenadas próprias, pode herdar do prédio caso o prédio tenha.
"""
import sys
import os
import re
import argparse
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.predio import Predio
from app.models.unidade import Unidade


_GOOGLE_LINK_EXPAND_CACHE = {}


def _expand_google_short_link(url: str, timeout_seconds: int = 8) -> str:
    s = (url or "").strip()
    if not s:
        return s
    if "maps.app.goo.gl" not in s and "goo.gl/maps" not in s:
        return s
    cached = _GOOGLE_LINK_EXPAND_CACHE.get(s)
    if cached is not None:
        return cached
    try:
        req = Request(s, headers={"User-Agent": "SIGUS-BackfillLatLng/1.0"})
        resp = urlopen(req, timeout=timeout_seconds)
        expanded = resp.geturl() or s
    except Exception:
        expanded = s
    _GOOGLE_LINK_EXPAND_CACHE[s] = expanded
    return expanded


def extrair_coords_google_maps(url: str):
    """
    Retorna (lat, lng) ou None.
    Suporta padrões comuns do Google Maps:
      - @lat,lng
      - !3dlat!4dlng
      - q=lat,lng / center=lat,lng / ll=lat,lng
    """
    if not url:
        return None
    s = str(url).strip()
    if not s:
        return None

    s = _expand_google_short_link(s)

    # Preferência:
    # - !3dlat!4dlng costuma ser o "pino" do lugar
    # - @lat,lng costuma ser o centro/câmera do mapa (pode não ser exatamente o local)
    patterns = [
        r"!3d(-?\d+(?:\.\d+)?)[^!]*!4d(-?\d+(?:\.\d+)?)",
        r"@(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)",
        r"(?:q|center|ll)=(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            try:
                lat = float(m.group(1))
                lng = float(m.group(2))
                return (lat, lng)
            except Exception:
                return None
    return None


def _is_missing(lat, lng) -> bool:
    return lat is None or lng is None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Não grava no banco; só imprime o que faria.")
    ap.add_argument("--limit", type=int, default=0, help="Limita quantos registros processar por tabela (0 = sem limite).")
    ap.add_argument("--no-expand", action="store_true", help="Não tenta expandir links curtos (menos HTTP; pode perder coords).")
    args = ap.parse_args()

    global _expand_google_short_link
    if args.no_expand:
        _expand_google_short_link = lambda url, timeout_seconds=8: (url or "").strip()

    app = create_app()
    with app.app_context():
        predios = Predio.query.filter(Predio.link_maps.isnot(None)).all()
        unidades = Unidade.query.filter(Unidade.link_maps.isnot(None)).all()

        if args.limit and args.limit > 0:
            predios = predios[: args.limit]
            unidades = unidades[: args.limit]

        p_ok = p_skip = 0
        for p in predios:
            if not _is_missing(p.latitude, p.longitude):
                p_skip += 1
                continue
            coords = extrair_coords_google_maps(p.link_maps)
            if not coords:
                continue
            lat, lng = coords
            if args.dry_run:
                print(f"[DRY] Predio {p.id} {p.nome!r}: ({lat}, {lng})")
            else:
                p.latitude = lat
                p.longitude = lng
            p_ok += 1

        u_ok = u_inherit = u_skip = 0
        for u in unidades:
            if not _is_missing(u.latitude, u.longitude):
                u_skip += 1
                continue
            coords = extrair_coords_google_maps(u.link_maps)
            if coords:
                lat, lng = coords
                if args.dry_run:
                    print(f"[DRY] Unidade {u.id} {u.nome!r}: ({lat}, {lng})")
                else:
                    u.latitude = lat
                    u.longitude = lng
                u_ok += 1
                continue

        # Herança (2ª passada): unidade sem coords herda do prédio se disponível
        unidades_sem = Unidade.query.filter(
            Unidade.predio_id.isnot(None),
            Unidade.latitude.is_(None),
            Unidade.longitude.is_(None),
        ).all()
        if args.limit and args.limit > 0:
            unidades_sem = unidades_sem[: args.limit]
        for u in unidades_sem:
            if not u.predio:
                continue
            if _is_missing(u.predio.latitude, u.predio.longitude):
                continue
            if args.dry_run:
                print(f"[DRY] Unidade {u.id} {u.nome!r}: herdaria do prédio {u.predio.id} ({u.predio.latitude}, {u.predio.longitude})")
            else:
                u.latitude = u.predio.latitude
                u.longitude = u.predio.longitude
            u_inherit += 1

        if not args.dry_run:
            db.session.commit()

        print(f"Predios atualizados: {p_ok} | já tinham: {p_skip}")
        print(f"Unidades atualizadas por link: {u_ok} | herdadas do prédio: {u_inherit} | já tinham: {u_skip}")


if __name__ == "__main__":
    main()

