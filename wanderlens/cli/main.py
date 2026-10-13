from __future__ import annotations

import argparse
from typing import Optional, Sequence

from wanderlens.config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wanderlens",
        description="Learn a travel taste profile from a photo archive and recommend destinations.",
    )
    parser.add_argument("--config", default=None, help="path to a YAML config file")
    parser.add_argument("--user", default="owner", help="user name to scope data to")
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="read photos and build the local archive")
    p_ingest.add_argument("--photos", default=None, help="photo folder (overrides config)")
    p_ingest.add_argument(
        "--tag",
        action="store_true",
        help="also run vision tagging on sampled photos (sends them to the VLM)",
    )
    p_ingest.add_argument(
        "--retag",
        action="store_true",
        help="re-run vision tagging even if subjects are already stored",
    )
    p_ingest.set_defaults(func=cmd_ingest)

    p_profile = sub.add_parser("profile", help="manage the taste profile")
    profile_sub = p_profile.add_subparsers(dest="profile_command")
    p_show = profile_sub.add_parser("show", help="show the taste profile")
    p_show.set_defaults(func=cmd_profile_show)
    p_profile.set_defaults(func=cmd_profile_show)

    p_rec = sub.add_parser("recommend", help="recommend new destinations")
    p_rec.add_argument("--count", type=int, default=5, help="number of recommendations")
    p_rec.add_argument(
        "--alpha",
        type=float,
        default=None,
        help="weight of embedding similarity vs attribute match (0..1; default from config, 0.25)",
    )
    p_rec.add_argument(
        "--no-media",
        action="store_true",
        help="skip fetching destination images, expanded descriptions, and region shapes",
    )
    p_rec.add_argument(
        "--explain-llm",
        action="store_true",
        help="synthesise the 'why' with the LLM (needs an API key); cached",
    )
    p_rec.add_argument(
        "--diversity",
        type=float,
        default=0.25,
        help="MMR diversity weight (0 = pure relevance, 1 = max variety)",
    )
    p_rec.add_argument(
        "--novelty",
        choices=["familiar", "balanced", "uncommon"],
        default="balanced",
        help="bias selection toward famous or uncommon places",
    )
    p_rec.set_defaults(func=cmd_recommend)

    p_eval = sub.add_parser("eval", help="hold-out evaluation of the taste profile")
    p_eval.add_argument("--holdout", default=None, help="visited place to hold out")
    p_eval.add_argument(
        "--synthetic",
        action="store_true",
        help="rank the reproducible synthetic gallery instead of the archive",
    )
    p_eval.add_argument("--k", type=int, default=3, help="cut-off for precision@k (synthetic)")
    p_eval.set_defaults(func=cmd_eval)

    p_serve = sub.add_parser("serve", help="run the local read-only web dashboard")
    p_serve.add_argument("--host", default="127.0.0.1", help="bind host (localhost only by default)")
    p_serve.add_argument("--port", type=int, default=8000, help="port to listen on")
    p_serve.set_defaults(func=cmd_serve)

    p_guide = sub.add_parser("guide", help="build rich travel guides for the recommended destinations")
    p_guide.add_argument("--count", type=int, default=None, help="number of destinations")
    p_guide.add_argument("--refresh", action="store_true", help="rebuild guides even if cached")
    p_guide.add_argument("--no-llm", action="store_true", help="skip the synthesised itinerary")
    p_guide.set_defaults(func=cmd_guide)

    return parser


def cmd_ingest(args: argparse.Namespace) -> int:
    from wanderlens.pipeline.ingest import run_ingest
    from wanderlens.pipeline.profile import run_profile

    config = load_config(args.config)
    if args.photos:
        config.photos_dir = config.photos_dir.__class__(args.photos)
    count = run_ingest(config, user_name=args.user)

    vision = None
    if args.tag:
        from wanderlens.models.vision import HostedVLM

        vision = HostedVLM(config.api_key, config.vlm_model)

    enricher = None
    if config.enrich_taste and config.api_key:
        from wanderlens.models.enricher import HostedTasteEnricher

        enricher = HostedTasteEnricher(config.api_key, config.llm_model)

    trips = run_profile(
        config, user_name=args.user, vision=vision, retag=args.retag, enricher=enricher
    )
    print(
        f"Ingested {count} new photo(s); built profile with {len(trips)} trip(s) "
        f"into {config.db_path}"
    )
    return 0


def cmd_profile_show(args: argparse.Namespace) -> int:
    from wanderlens.pipeline.profile import show_profile

    config = load_config(args.config)
    text = show_profile(config, user_name=args.user)
    print(text)
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    from wanderlens.pipeline.recommend import run_recommend

    config = load_config(args.config)
    explainer = None
    if args.explain_llm or config.explain_llm:
        if config.api_key:
            from wanderlens.models.ranker import HostedExplanationSynthesizer

            explainer = HostedExplanationSynthesizer(config.api_key, config.llm_model)
        else:
            print("No API key configured; using the deterministic explanation.")
    recs = run_recommend(
        config,
        user_name=args.user,
        count=args.count,
        alpha=args.alpha if args.alpha is not None else config.alpha,
        media=not args.no_media,
        explainer=explainer,
        diversity=args.diversity,
        novelty=args.novelty,
        popularity=True,
    )
    if not recs:
        print("No recommendations.")
        return 0
    for rec in recs:
        emb = f"{rec.embedding_score:.3f}" if rec.embedding_score is not None else "-"
        attr = f"{rec.attribute_score:.3f}" if rec.attribute_score is not None else "-"
        print(
            f"{rec.rank}. {rec.destination.name} ({rec.destination.country}) "
            f"- {rec.score:.3f}  [emb {emb} / attr {attr}]"
        )
        if rec.explanation:
            print(f"   {rec.explanation}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    from wanderlens.pipeline.evaluate import run_eval, run_synthetic_eval

    config = load_config(args.config)
    if args.synthetic:
        print(run_synthetic_eval(k=args.k))
        return 0
    print(run_eval(config, user_name=args.user, holdout=args.holdout))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from wanderlens.web.app import create_app

    config = load_config(args.config)
    app = create_app(config, user_name=args.user)
    print(f"Serving Wanderlens on http://{args.host}:{args.port} (Ctrl-C to stop)")
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def cmd_guide(args: argparse.Namespace) -> int:
    from wanderlens.pipeline.guide import run_guide

    config = load_config(args.config)
    synthesizer = None
    if not args.no_llm:
        if config.api_key:
            from wanderlens.models.ranker import HostedItinerarySynthesizer

            synthesizer = HostedItinerarySynthesizer(config.api_key, config.llm_model)
        else:
            print("No API key configured; building guides without a synthesised itinerary.")
    built = run_guide(
        config,
        user_name=args.user,
        count=args.count,
        refresh=args.refresh,
        synthesizer=synthesizer,
    )
    print(f"Built guides for {built} destination(s) into {config.db_path}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)
