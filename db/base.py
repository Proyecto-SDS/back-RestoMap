import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

def _load_dotenv(path="../.env"):
    env = {}
    try:
        here = os.path.dirname(__file__)
        p = os.path.normpath(os.path.join(here, path))
        with open(p, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env

_env = _load_dotenv()

def _get(key_candidates, default=None):
    for k in key_candidates:
        v = _env.get(k) or os.getenv(k)
        if v is not None and v != "":
            return v
    return default

DB_USER = _get(["DB_USER"], None)
DB_PASSWORD = _get(["DB_PASSWORD"], None)
DB_HOST = _get(["DB_HOST"], "localhost")
DB_PORT = _get(["DB_PORT"], "5432")
DB_NAME = _get(["DB_NAME"], None)

_faltante = []

if not DB_USER:
    _faltante.append("DB_USER")
if not DB_PASSWORD:
    _faltante.append("DB_PASSWORD")
if not DB_NAME:
    _faltante.append("DB_NAME")
if _faltante:
    raise RuntimeError(f"Faltan variables de entorno necesarias: {', '.join(_faltante)}. ")
try:
    port_int = int(DB_PORT) if DB_PORT is not None else 5432
except Exception:
    port_int = 5432

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{port_int}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
Base = declarative_base()