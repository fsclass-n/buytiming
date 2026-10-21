"""주간 가격 리포트 (RPA 작업 BOT-04, 매주 월 07:00): pandas 집계 + Seaborn 차트 → 엑셀

실행: python -m app.jobs.weekly_report --out reports/
"""
import argparse
import io
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from openpyxl.drawing.image import Image as XLImage  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from ..config import now_local  # noqa: E402
from ..models import Product  # noqa: E402
from ..services.pricing import daily_lowest_all  # noqa: E402
from ..services.timing import latest_prediction  # noqa: E402

plt.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def build_report(db: Session) -> tuple[bytes, str]:
    products = {p.id: p for p in db.execute(select(Product)).scalars()}
    pv = daily_lowest_all(db, days=14)
    rows = []
    for pid, p in products.items():
        if pid not in pv.columns:
            continue
        col = pv[pid].dropna()
        this_week, last_week = col.iloc[-7:], col.iloc[-14:-7]
        tp = latest_prediction(db, pid)
        rows.append({"상품": p.name, "카테고리": p.category, "이번 주 최저가": int(this_week.min()) if len(this_week) else None,
                     "지난주 최저가": int(last_week.min()) if len(last_week) else None,
                     "현재 판정": tp.label if tp else "-", "적기 점수": tp.score if tp else None})
    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary["변동률(%)"] = ((summary["이번 주 최저가"] / summary["지난주 최저가"] - 1) * 100).round(1)
    daily = pv.rename(columns={pid: products[pid].name for pid in pv.columns if pid in products})
    daily.index = daily.index.date

    fig, ax = plt.subplots(figsize=(8, 4))
    if not summary.empty:
        sns.barplot(data=summary.sort_values("변동률(%)"), x="변동률(%)", y="상품", hue="카테고리", ax=ax)
    ax.set_title("관심 상품 주간 최저가 변동률")
    fig.tight_layout()
    img = io.BytesIO()
    fig.savefig(img, format="png", dpi=110)
    plt.close(fig)

    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="주간 요약", index=False)
        daily.to_excel(xw, sheet_name="일별 최저가")
        ws = xw.book.create_sheet("차트")
        img.seek(0)
        ws.add_image(XLImage(img), "A1")
    name = f"weekly_report_{now_local():%Y%m%d}.xlsx"
    return out.getvalue(), name


if __name__ == "__main__":
    from ..database import SessionLocal, init_db

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()
    init_db()
    with SessionLocal() as session:
        data, fname = build_report(session)
    path = pathlib.Path(args.out)
    path.mkdir(parents=True, exist_ok=True)
    (path / fname).write_bytes(data)
    print(f"saved {path / fname}")
