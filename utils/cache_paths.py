from pathlib import Path


def commenter_variant_from_instance(commenter) -> str:
    """Derive commenter variant name from instance type."""
    if commenter is None:
        return "none"
    cls_name = commenter.__class__.__name__
    if cls_name == 'Commenter':
        return 'storyboard'
    if cls_name == 'CommenterTextOnly':
        return 'text-only'
    if cls_name == 'CommenterScreenshotOnly':
        return 'screenshot-only'
    return cls_name.lower()


def comment_cache_dir(base_dir: Path, v0_dir: str, commenter_variant: str, model: str, app: str) -> Path:
    scope = v0_dir if v0_dir else 'default'
    return base_dir / 'v0' / scope / 'comments' / commenter_variant / model / app


def v1_cache_dir(base_dir: Path, v0_dir: str, revision_variant: str, model: str, app: str) -> Path:
    scope = v0_dir if v0_dir else 'default'
    return base_dir / 'progress' / 'stage3_v1' / scope / revision_variant / model / app

