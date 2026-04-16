import gzip
import base64
import uuid
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Taille maximale d'un chunk base64 : 4 Mo (largement sous la limite ngrok de 10 Mo)
CHUNK_SIZE = 4 * 1024 * 1024


def _compress_and_split(raw_bytes: bytes) -> tuple:
    """
    Compresse les bytes bruts avec gzip puis découpe en chunks base64.
    Retourne (chunks: list[str], transfer_id: str, total: int)
    """
    compressed  = gzip.compress(raw_bytes, compresslevel=6)
    b64         = base64.b64encode(compressed).decode("utf-8")
    chunks      = [b64[i:i + CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
    transfer_id = uuid.uuid4().hex
    return chunks, transfer_id, len(chunks)


def _reassemble_and_decompress(chunks: list) -> bytes:
    """
    Recolle les chunks base64 et décompresse.
    Retourne les bytes bruts du .bin.
    """
    b64_full = "".join(chunks)
    raw      = base64.b64decode(b64_full.encode("utf-8"))
    return gzip.decompress(raw)


def upload_model(model_file: str, api_base_url: str, headers: dict,
                 print_fn=print) -> str:
    """
    Envoie le modèle local au serveur en plusieurs chunks compressés.
    Retourne le transfer_id à inclure dans la requête suivante.
    """
    with open(model_file, "rb") as f:
        raw = f.read()

    chunks, transfer_id, total = _compress_and_split(raw)

    size_ko = len(raw) // 1024
    print_fn(f"  Upload modèle : {size_ko} Ko → {total} chunk(s) compressé(s)")

    url = api_base_url.rstrip("/") + "/upload_chunk"

    for idx, chunk in enumerate(chunks):
        resp = requests.post(
            url,
            json={
                "transfer_id":  transfer_id,
                "chunk_idx":    idx,
                "total_chunks": total,
                "data":         chunk,
                "compressed":   True,
            },
            headers=headers,
            timeout=60,
            verify=False,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur upload chunk {idx}/{total - 1} : {resp.status_code} {resp.text}"
            )
        print_fn(f"  Envoi chunk {idx + 1}/{total}...")

    print_fn(f"  Upload terminé ({total} chunk(s)).")
    return transfer_id


def download_model(download_id: str, total_chunks: int,
                   api_base_url: str, headers: dict,
                   print_fn=print) -> bytes:
    """
    Télécharge le modèle depuis le serveur chunk par chunk.
    Retourne les bytes bruts du .bin (décompressé).
    """
    print_fn(f"  Réception modèle : {total_chunks} chunk(s)...")

    base_url = api_base_url.rstrip("/")
    chunks   = []

    for idx in range(total_chunks):
        url  = f"{base_url}/download_chunk/{download_id}/{idx}"
        resp = requests.get(url, headers=headers, timeout=60, verify=False)

        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur download chunk {idx}/{total_chunks - 1} : "
                f"{resp.status_code} {resp.text}"
            )

        data = resp.json()
        chunks.append(data["data"])
        print_fn(f"  Chunk {idx + 1}/{total_chunks} reçu.")

    raw = _reassemble_and_decompress(chunks)
    print_fn(f"  Modèle reçu ({len(raw) // 1024} Ko non compressé).")
    return raw