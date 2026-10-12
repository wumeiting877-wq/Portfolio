from pathlib import Path


def test_alembic_ini_exists() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    assert (backend_root / "alembic.ini").is_file()
    assert (backend_root / "alembic" / "env.py").is_file()
    assert (backend_root / "alembic" / "versions").is_dir()


def test_gate2_migration_file_exists() -> None:
    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    assert (versions / "0003_gate2_projects.py").is_file()


def test_gate3_migration_file_exists() -> None:
    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    assert (versions / "0004_gate3_resources.py").is_file()


def test_gate6_migration_file_exists() -> None:
    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    assert (versions / "0006_gate6_enterprise.py").is_file()
