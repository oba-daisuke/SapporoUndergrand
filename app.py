import os
import glob
import streamlit as st
import pandas as pd
from datetime import datetime, date, time as dtime, timedelta
from zoneinfo import ZoneInfo

st.set_page_config(page_title="地下鉄 到着案内", layout="wide")
JST = ZoneInfo("Asia/Tokyo")
TIMETABLE_DIR = "timetables"  # 駅CSV置き場

AUTO_REFRESH_SEC = 15
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="refresh")
except Exception:
    pass


def is_weekend_or_holiday(d: date) -> bool:
    """土日祝なら True。jpholiday が無ければ土日だけ判定。"""
    # weekend
    if d.weekday() >= 5:
        return True
    # holiday (Japan)
    try:
        import jpholiday
        return jpholiday.is_holiday(d)
    except Exception:
        return False


def parse_hhmm_to_dt(hhmm: str, base_date: date) -> datetime:
    hh, mm = str(hhmm).split(":")
    return datetime.combine(base_date, dtime(int(hh), int(mm)), tzinfo=JST)


@st.cache_data
def load_timetable_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"line", "station", "direction", "day_type", "time"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSVに必要な列が足りません: {missing}")

    # optional columns
    if "dest" not in df.columns:
        df["dest"] = ""
    if "remark" not in df.columns:
        df["remark"] = ""

    # 正規化
    df["line"] = df["line"].astype(str)
    df["station"] = df["station"].astype(str)
    df["direction"] = df["direction"].astype(str)
    df["day_type"] = df["day_type"].astype(str)
    df["time"] = df["time"].astype(str)

    return df


def list_csv_files() -> list[str]:
    os.makedirs(TIMETABLE_DIR, exist_ok=True)
    return sorted(glob.glob(os.path.join(TIMETABLE_DIR, "*.csv")))


def parse_filename(path: str):
    """
    期待: timetables/南北線_麻生_真駒内方面.csv
    => (line, station, direction)
    うまく分割できなければ (None, None, None)
    """
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    parts = name.split("_")
    if len(parts) >= 3:
        return parts[0], parts[1], "_".join(parts[2:])
    return None, None, None


def next_trains(df: pd.DataFrame, now: datetime, n=3) -> pd.DataFrame:
    """now以降の次列車n本を返す。当日と翌日の日付をまたがって正しく処理。"""
    tmp = df.copy()
    
    # 当日と翌日の両方の日付でdatetime列を作る
    today = now.date()
    tomorrow = (now + timedelta(days=1)).date()
    
    tmp["dt_today"] = tmp["time"].apply(lambda x: parse_hhmm_to_dt(x, today))
    tmp["dt_tomorrow"] = tmp["time"].apply(lambda x: parse_hhmm_to_dt(x, tomorrow))
    
    # 当日の時刻がnow以降なら当日、そうでなければ翌日を使う
    tmp["dt"] = tmp.apply(
        lambda row: row["dt_today"] if row["dt_today"] >= now else row["dt_tomorrow"],
        axis=1
    )
    
    future = tmp[tmp["dt"] >= now].sort_values("dt").head(n)
    if future.empty:
        return future

    future = future.copy()
    future["in_min"] = ((future["dt"] - now).dt.total_seconds() / 60).round().astype(int)
    return future[["time", "dest", "remark", "in_min"]]


def big_card(title: str, rows: pd.DataFrame):
    st.markdown(
        f"""
        <div style="
            border: 3px solid #222;
            border-radius: 18px;
            padding: 18px 18px 10px 18px;
            margin-bottom: 14px;
            background: #fff;
        ">
          <div style="font-size: 30px; font-weight: 800; margin-bottom: 8px;">{title}</div>
        """,
        unsafe_allow_html=True,
    )

    if rows is None or rows.empty:
        st.markdown(
            """
            <div style="font-size: 26px; font-weight: 700; padding: 10px 0 16px 0;">
              次の列車が見つかりません
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for _, r in rows.iterrows():
            t = str(r["time"])
            dest = str(r.get("dest", "")).strip() or "—"
            remark = str(r.get("remark", "")).strip()
            if remark.lower() == "nan":
                remark = ""
            mins = int(r["in_min"])

            right = f"あと {mins} 分"
            left_sub = f"({dest})"
            if remark:
                left_sub += f"  <span style='color:#B00; font-weight:800;'>[{remark}]</span>"

            st.markdown(
                f"""
                <div style="
                    display:flex; justify-content:space-between; align-items:baseline;
                    padding: 10px 0; border-top: 1px solid #ddd;
                ">
                  <div style="font-size: 26px; font-weight: 750;">
                    {t} <span style="font-size:18px; font-weight:600; color:#444;">{left_sub}</span>
                  </div>
                  <div style="font-size: 34px; font-weight: 900;">
                    {right}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.title("設定")

now = datetime.now(JST)
st.sidebar.write("現在時刻")
st.sidebar.markdown(f"**{now.strftime('%Y-%m-%d %H:%M:%S')}**")

# day_type auto
effective_date = (now + timedelta(days=1)).date() if now.hour >= 1 else now.date()
auto_day_type = "weekend_holiday" if is_weekend_or_holiday(effective_date) else "weekday"
st.sidebar.write("適用ダイヤ判定")
st.sidebar.markdown(f"**{'土日祝' if auto_day_type=='weekend_holiday' else '平日'}**")

# たまに手動で切り替えたい人向け
day_type = st.sidebar.radio(
    "使用するダイヤ",
    options=["auto", "weekday", "weekend_holiday"],
    index=0,
    help="autoは祝日も判定（jpholidayが入っている場合）",
)
if day_type == "auto":
    day_type = auto_day_type

n_trains = st.sidebar.slider("表示する本数", 1, 5, 2)

# CSV一覧を読み、駅・路線・方面の候補を出す
files = list_csv_files()
if not files:
    st.warning(
        f"`{TIMETABLE_DIR}/` にCSVがありません。\n\n"
        "例: `timetables/南北線_麻生_真駒内方面.csv` を置いてください。"
    )
    st.stop()

meta = []
for p in files:
    line, station, direction = parse_filename(p)
    meta.append({"path": p, "line": line or "?", "station": station or "?", "direction": direction or "?"})
meta_df = pd.DataFrame(meta)

# 南北線の場合、デフォルトでさっぽろ→麻生方面 と 麻生→真駒内方面 を横に並べて表示
if "南北線" in meta_df["line"].values:
    nankoku_meta = meta_df[meta_df["line"] == "南北線"]
    sapporo_asahikawa = nankoku_meta[(nankoku_meta["station"] == "さっぽろ") & (nankoku_meta["direction"] == "麻生方面")]
    asahikawa_makomanai = nankoku_meta[(nankoku_meta["station"] == "麻生") & (nankoku_meta["direction"] == "真駒内方面")]
    
    if not sapporo_asahikawa.empty and not asahikawa_makomanai.empty:
        col1, col2 = st.columns(2)
        
        # さっぽろ→麻生方面
        with col1:
            path1 = sapporo_asahikawa.iloc[0]["path"]
            try:
                df1_all = load_timetable_csv(path1)
                df1 = df1_all[df1_all["day_type"] == day_type].copy()
                if not df1.empty:
                    title1 = f"南北線 / さっぽろ / 麻生方面（{'土日祝' if day_type=='weekend_holiday' else '平日'}）"
                    nxt1 = next_trains(df1, now, n=n_trains)
                    big_card(title1, nxt1)
            except Exception as e:
                st.error(f"CSV読み込み失敗: {e}")
        
        # 麻生→真駒内方面
        with col2:
            path2 = asahikawa_makomanai.iloc[0]["path"]
            try:
                df2_all = load_timetable_csv(path2)
                df2 = df2_all[df2_all["day_type"] == day_type].copy()
                if not df2.empty:
                    title2 = f"南北線 / 麻生 / 真駒内方面（{'土日祝' if day_type=='weekend_holiday' else '平日'}）"
                    nxt2 = next_trains(df2, now, n=n_trains)
                    big_card(title2, nxt2)
            except Exception as e:
                st.error(f"CSV読み込み失敗: {e}")
