from hashlib import sha1


def _slug_v0(v0_dir: str) -> str:
    if not v0_dir:
        return "default"
    # Keep it simple and deterministic
    return str(v0_dir).replace("/", "_").replace(" ", "-")


def build_run_key(revision_type: str, commenter: str, v0_dir: str) -> str:
    """Deterministic namespace key for a Stage 3 configuration.

    Format: rev-<revision_type>__commenter-<commenter>__v0-<v0_slug>
    """
    return f"rev-{revision_type}__commenter-{commenter}__v0-{_slug_v0(v0_dir)}"


def short_run_key(run_key: str) -> str:
    return sha1(run_key.encode("utf-8")).hexdigest()[:8]

