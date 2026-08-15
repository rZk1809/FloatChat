"""Inspect a disposable Chroma copy without touching a repository store."""

from __future__ import annotations

import argparse
from pathlib import Path

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTION = "argo_profiles_ollama"


def inspect_copy(copy_path: Path, collection_name: str, limit: int) -> None:
    resolved = copy_path.expanduser().resolve(strict=True)
    if resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents:
        raise ValueError("Refusing to open a Chroma store inside the repository")
    if not resolved.is_dir():
        raise ValueError("Inspection path must be a directory")

    client = chromadb.PersistentClient(path=str(resolved))
    collection = client.get_collection(name=collection_name)
    count = collection.count()
    sample = collection.get(limit=min(limit, count), include=["documents", "metadatas"])

    print(f"Collection: {collection_name}")
    print(f"Count: {count}")
    print(f"Sample IDs: {sample['ids']}")
    print(f"Sample metadata: {sample['metadatas']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy-path", required=True, type=Path)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--limit", type=int, choices=range(1, 11), default=3)
    args = parser.parse_args()
    inspect_copy(args.copy_path, args.collection, args.limit)


if __name__ == "__main__":
    main()
