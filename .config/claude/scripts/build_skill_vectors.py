#!/usr/bin/env python3
"""Build vector index from Claude skills.

Indexes:
- Skill files from ~/.claude/skills/
- Extracts name, description, trigger keywords, and content

Usage:
    python ~/.claude/scripts/build_skill_vectors.py [--rebuild]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional, List

import chromadb
import chromadb.errors
from sentence_transformers import SentenceTransformer


def parse_skill(skill_path: Path) -> Optional[dict]:
    """Parse a skill file and extract metadata + content."""
    content = skill_path.read_text()

    # Extract YAML frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)
    body = content[frontmatter_match.end():]

    # Parse frontmatter fields
    skill = {
        'path': str(skill_path),
        'filename': skill_path.name,
    }

    for field in ['name', 'description', 'invocation']:
        if m := re.search(rf'^{field}:\s*(.+)$', frontmatter, re.MULTILINE):
            skill[field] = m.group(1).strip().strip('"\'')

    if not skill.get('name'):
        skill['name'] = skill_path.stem

    # Extract trigger keywords from body (look for patterns like "batch", ".bat", etc)
    triggers = set()
    trigger_patterns = [
        r'`([^`]+)`',  # backtick code
        r'\|([^|]+)\|',  # table cells
    ]
    for pattern in trigger_patterns:
        for match in re.finditer(pattern, body):
            term = match.group(1).strip()
            if len(term) > 2 and len(term) < 30:
                triggers.add(term.lower())

    skill['triggers'] = list(triggers)[:50]  # Cap at 50
    skill['body'] = body

    return skill


def chunk_text(text: str, max_tokens: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    if len(words) <= max_tokens:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


def index_skills(skills_dir: Path, collection, model) -> int:
    """Index all skill files."""
    count = 0

    for skill_path in skills_dir.glob('*.md'):
        if skill_path.name in ('SKILL-INDEX.md', 'README.md'):
            continue

        skill = parse_skill(skill_path)
        if not skill:
            continue

        # Create embedding text: name + description + triggers + body
        embed_parts = []
        if skill.get('name'):
            embed_parts.append(f"Skill: {skill['name']}")
        if skill.get('description'):
            embed_parts.append(f"Description: {skill['description']}")
        if skill.get('triggers'):
            embed_parts.append(f"Keywords: {', '.join(skill['triggers'][:20])}")
        if skill.get('body'):
            embed_parts.append(skill['body'])

        full_text = '\n'.join(embed_parts)
        chunks = chunk_text(full_text)

        for i, chunk in enumerate(chunks):
            doc_id = f"{skill['name']}_{i}" if len(chunks) > 1 else skill['name']

            metadata = {
                'name': skill.get('name', ''),
                'description': skill.get('description', ''),
                'path': skill.get('path', ''),
                'filename': skill.get('filename', ''),
                'invocation': skill.get('invocation', ''),
                'triggers': ','.join(skill.get('triggers', [])[:20]),
            }

            embedding = model.encode(chunk).tolist()

            collection.add(
                ids=[doc_id],
                documents=[chunk],
                metadatas=[metadata],
                embeddings=[embedding]
            )
            count += 1
            print(f"  Indexed: {skill['name']} (chunk {i+1}/{len(chunks)})")

    return count


def main():
    parser = argparse.ArgumentParser(description='Build vector index from skills')
    parser.add_argument('--rebuild', action='store_true', help='Delete and rebuild index')
    args = parser.parse_args()

    # Paths
    skills_dir = Path.home() / '.claude' / 'skills'
    vectors_dir = Path.home() / '.claude' / 'vectors'

    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    vectors_dir.mkdir(parents=True, exist_ok=True)

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Initializing vector store...")
    client = chromadb.PersistentClient(path=str(vectors_dir))

    if args.rebuild:
        try:
            client.delete_collection('skills')
            print("Deleted existing collection")
        except (ValueError, chromadb.errors.NotFoundError):
            pass

    collection = client.get_or_create_collection(
        name='skills',
        metadata={'hnsw:space': 'cosine'}
    )

    existing = collection.count()
    if existing > 0 and not args.rebuild:
        print(f"Collection has {existing} documents. Use --rebuild to reindex.")
        sys.exit(0)

    print(f"Indexing skills from {skills_dir}...")
    n = index_skills(skills_dir, collection, model)

    print(f"\nTotal: {n} chunks indexed")
    print(f"Vector store: {vectors_dir}")


if __name__ == '__main__':
    main()
