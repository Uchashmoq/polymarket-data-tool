from config import *
import gzip
import json
import logging
from pathlib import Path
import websockets
import asyncio
import requests

logger = logging.getLogger(__name__)


class RawWsJsonlWriter:
    def __init__(self, data_dir: str = "data", flush_every: int = 1000) -> None:
        self.data_dir = Path(data_dir)
        self.files = {}
        self.write_counts = {}
        self.flush_every = flush_every

    def write(self, event_slug: str, market_slug: str, payload: dict) -> None:
        key = (event_slug, market_slug)
        if key not in self.files:
            market_dir = self.data_dir / event_slug / market_slug
            market_dir.mkdir(parents=True, exist_ok=True)
            path = market_dir / "ws_raw.jsonl.gz"
            self.files[key] = gzip.open(path, "at", encoding="utf-8")
            self.write_counts[key] = 0
            logger.info("opened raw websocket file path=%s", path)

        self.files[key].write(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        self.write_counts[key] += 1
        if self.flush_every > 0 and self.write_counts[key] % self.flush_every == 0:
            self.files[key].flush()
            logger.info(
                "flushed raw websocket file event_slug=%s market_slug=%s writes=%d",
                event_slug,
                market_slug,
                self.write_counts[key],
            )

    def close(self) -> None:
        for file in self.files.values():
            file.close()
        self.files.clear()
        self.write_counts.clear()


async def connect_market_ws(listening_tokens: dict, market_condition_id: dict) -> None:
    token_ids = list(listening_tokens.keys())
    endpoint = WS_ENDPOINT + "/market"
    raw_writer = RawWsJsonlWriter()
    msg = json.dumps(
        {
            "assets_ids": token_ids,
            "type": "market",
            "custom_feature_enabled": False,
        }
    )
    reconnect_delay = 1
    logger.info("prepared market websocket subscription tokens=%d", len(token_ids))
    try:
        while True:
            try:
                logger.info("connecting market websocket endpoint=%s", endpoint)
                async with websockets.connect(
                    endpoint, ping_interval=5, ping_timeout=None
                ) as w:
                    await w.send(msg)
                    logger.info("market websocket subscribed tokens=%d", len(token_ids))

                    reconnect_delay = 1
                    while True:
                        resp = await w.recv()
                        j = json.loads(resp)
                        if not isinstance(j, list):
                            j = [j]
                        for p in j:
                            condition_id = p.get("market")
                            if condition_id is None:
                                logger.warning(
                                    "skipping websocket event without market payload=%s",
                                    p,
                                )
                                continue

                            market_info = market_condition_id.get(condition_id)
                            if market_info is None:
                                logger.warning(
                                    "skipping websocket event for unknown condition_id=%s",
                                    condition_id,
                                )
                                continue

                            event_slug = market_info["event_slug"]
                            market = market_info["market"]
                            market_slug = market["slug"]
                            raw_writer.write(event_slug, market_slug, p)

            except (websockets.ConnectionClosed, TimeoutError, OSError) as e:
                logger.warning(
                    "market websocket disconnected error=%r reconnect_delay=%s",
                    e,
                    reconnect_delay,
                )
            except Exception as e:
                logger.exception(
                    "market websocket unexpected error=%r reconnect_delay=%s",
                    e,
                    reconnect_delay,
                )

            await asyncio.sleep(reconnect_delay)
    finally:
        raw_writer.close()


listening_events = ["highest-temperature-in-seoul-on-june-28-2026"]


async def main():
    listening_tokens = {}
    market_condition_id = {}
    for event_slug in listening_events:
        event_info_path = Path("data") / event_slug / "info.json"
        if event_info_path.exists():
            logger.info("loading cached event path=%s", event_info_path)
            event = json.loads(event_info_path.read_text(encoding="utf-8"))
        else:
            logger.info("fetching event slug=%s", event_slug)
            event = requests.get(GAMMA_API + "/events/slug/" + event_slug).json()
            event_info_path.parent.mkdir(parents=True, exist_ok=True)
            event_info_path.write_text(
                json.dumps(event, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
        logger.info(
            "loaded event slug=%s markets=%d",
            event["slug"],
            len(event["markets"]),
        )
        for market in event["markets"]:
            market_condition_id[market["conditionId"]] = {
                "event_slug": event["slug"],
                "market": market,
            }
            token_ids = json.loads(market["clobTokenIds"])
            logger.info(
                "loaded market slug=%s condition_id=%s tokens=%d",
                market["slug"],
                market["conditionId"],
                len(token_ids),
            )
            for id in token_ids:
                listening_tokens[id] = {
                    "event_slug": event["slug"],
                    "market_slug": market["slug"],
                }
    logger.info("starting market websocket tokens=%d", len(listening_tokens))
    t1 = asyncio.create_task(connect_market_ws(listening_tokens, market_condition_id))
    await asyncio.gather(t1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())
