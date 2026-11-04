import json
import os
import pathlib
from dataclasses import dataclass, field

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")


@dataclass(frozen=True)
class Config:
    api_base_url: str = field(default_factory=lambda: os.getenv("RPA_TARGET_API", "http://localhost:8000").rstrip("/"))
    rpa_api_key: str = field(default_factory=lambda: os.getenv("RPA_API_KEY", ""))
    request_interval_sec: float = field(default_factory=lambda: float(os.getenv("REQUEST_INTERVAL_SEC", "3")))
    user_agent: str = field(default_factory=lambda: os.getenv("COLLECTOR_USER_AGENT", "BuyTimingBot/1.0 (+contact: team3@buytiming.example)"))
    simulate: bool = field(default_factory=lambda: os.getenv("SIMULATE_MALLS", "true").lower() == "true")
    mall_config_path: pathlib.Path = field(default_factory=lambda: pathlib.Path(os.getenv("MALL_CONFIG", ROOT / "malls.json")))
    public_api_url: str = field(default_factory=lambda: os.getenv("KCA_API_URL", ""))
    public_api_key: str = field(default_factory=lambda: os.getenv("DATA_GO_KR_KEY", ""))
    public_map_path: pathlib.Path = field(default_factory=lambda: pathlib.Path(os.getenv("PUBLIC_PRICE_MAP", ROOT / "public_price_map.json")))
    report_dir: pathlib.Path = field(default_factory=lambda: pathlib.Path(os.getenv("REPORT_DIR", ROOT / "reports")))
    tz: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Seoul"))
    # 네이버 쇼핑 검색 OpenAPI (developers.naver.com) — 값이 있으면 '네이버쇼핑' 가격을 함께 수집
    naver_client_id: str = field(default_factory=lambda: os.getenv("NAVER_CLIENT_ID", ""))
    naver_client_secret: str = field(default_factory=lambda: os.getenv("NAVER_CLIENT_SECRET", ""))
    # AWS S3 (선택) — 값이 있으면 수집 원본·주간 리포트를 업로드
    s3_bucket: str = field(default_factory=lambda: os.getenv("S3_BUCKET", ""))
    s3_prefix: str = field(default_factory=lambda: os.getenv("S3_PREFIX", "buytiming").strip("/"))
    aws_region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "ap-northeast-2"))

    @property
    def naver_enabled(self) -> bool:
        return bool(self.naver_client_id and self.naver_client_secret)

    def mall_rules(self) -> dict:
        if self.mall_config_path.exists():
            return json.loads(self.mall_config_path.read_text(encoding="utf-8"))
        return {}
