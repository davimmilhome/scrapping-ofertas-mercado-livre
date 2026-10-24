"""Compatibilidade: python main.py usa a CLI do pacote."""

from offers_spider.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
