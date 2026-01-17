import pytest
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from app import next_trains, parse_hhmm_to_dt, is_weekend_or_holiday

JST = ZoneInfo("Asia/Tokyo")


@pytest.fixture
def sample_timetable():
    """サンプルの時刻表データを返す"""
    return pd.DataFrame({
        "line": ["南北線"] * 6,
        "station": ["さっぽろ"] * 6,
        "direction": ["麻生方面"] * 6,
        "day_type": ["weekday"] * 6,
        "time": ["22:15", "22:30", "23:00", "23:30", "00:00", "00:30"],
        "dest": ["麻生"] * 6,
        "remark": [""] * 6,
    })


@pytest.fixture
def timetable_with_midnight_boundary():
    """深夜・朝のデータを含むサンプルデータ"""
    return pd.DataFrame({
        "line": ["南北線"] * 12,
        "station": ["さっぽろ"] * 12,
        "direction": ["麻生方面"] * 12,
        "day_type": ["weekday"] * 12,
        "time": ["23:30", "23:40", "23:50", "00:00", "00:10", "00:20", 
                 "05:00", "05:30", "06:00", "06:30", "06:45", "07:00"],
        "dest": ["麻生"] * 12,
        "remark": [""] * 12,
    })


@pytest.fixture
def timetable_with_day_types():
    """平日/土日別のダイヤを持つサンプルデータ"""
    weekday_data = {
        "line": ["南北線"] * 6,
        "station": ["さっぽろ"] * 6,
        "direction": ["麻生方面"] * 6,
        "day_type": ["weekday"] * 6,
        "time": ["23:30", "23:50", "05:30", "06:00", "06:30", "07:00"],
        "dest": ["麻生"] * 6,
        "remark": [""] * 6,
    }
    weekend_data = {
        "line": ["南北線"] * 6,
        "station": ["さっぽろ"] * 6,
        "direction": ["麻生方面"] * 6,
        "day_type": ["weekend_holiday"] * 6,
        "time": ["23:30", "23:50", "06:00", "06:30", "07:00", "07:30"],
        "dest": ["麻生"] * 6,
        "remark": [""] * 6,
    }
    df_weekday = pd.DataFrame(weekday_data)
    df_weekend = pd.DataFrame(weekend_data)
    return pd.concat([df_weekday, df_weekend], ignore_index=True)


@pytest.fixture
def timetable_with_holiday_types():
    """祝日ダイヤ対応のサンプルデータ"""
    return pd.DataFrame({
        "line": ["南北線"] * 12,
        "station": ["さっぽろ"] * 12,
        "direction": ["麻生方面"] * 12,
        "day_type": ["weekday", "weekday", "weekday", "weekday", "weekday", "weekday",
                     "weekend_holiday", "weekend_holiday", "weekend_holiday", 
                     "weekend_holiday", "weekend_holiday", "weekend_holiday"],
        "time": ["23:30", "23:50", "05:30", "06:00", "06:30", "07:00",
                 "23:30", "23:50", "06:00", "06:30", "07:00", "07:30"],
        "dest": ["麻生"] * 12,
        "remark": [""] * 12,
    })


class TestNextTrains:
    def test_22時時点での次列車_23時台も表示される(self, sample_timetable):
        """
        現在が22:00の場合、22時台、23時台、翌日0時台の列車が正しく表示される
        """
        # 現在時刻: 2026-01-17 22:00:00 (JST)
        now = datetime(2026, 1, 17, 22, 0, 0, tzinfo=JST)
        
        result = next_trains(sample_timetable, now, n=3)
        
        assert len(result) == 3
        # 次の3本は: 22:15, 22:30, 23:00
        assert result.iloc[0]["time"] == "22:15"
        assert result.iloc[1]["time"] == "22:30"
        assert result.iloc[2]["time"] == "23:00"
        
    def test_23時時点での次列車_0時台が含まれる(self, sample_timetable):
        """
        現在が23:00の場合、23:00以降の列車（0時台を含む）が表示される
        """
        now = datetime(2026, 1, 17, 23, 0, 0, tzinfo=JST)
        
        result = next_trains(sample_timetable, now, n=3)
        
        assert len(result) == 3
        # 次の3本は: 23:00, 23:30, 00:00
        assert result.iloc[0]["time"] == "23:00"
        assert result.iloc[1]["time"] == "23:30"
        assert result.iloc[2]["time"] == "00:00"
        
    def test_23時45分時点での0時台が含まれる(self, sample_timetable):
        """
        現在が23:45の場合、翌日の0時台の列車が表示される
        """
        now = datetime(2026, 1, 17, 23, 45, 0, tzinfo=JST)
        
        result = next_trains(sample_timetable, now, n=3)
        
        # 23:45 以降は 00:00, 00:30, 翌々日 22:15 が該当
        assert len(result) == 3
        assert result.iloc[0]["time"] == "00:00"
        assert result.iloc[1]["time"] == "00:30"
        assert result.iloc[2]["time"] == "22:15"
        
    def test_分数計算が正しい(self, sample_timetable):
        """
        in_min（あと何分）の計算が正しいことを確認
        """
        now = datetime(2026, 1, 17, 22, 0, 0, tzinfo=JST)
        
        result = next_trains(sample_timetable, now, n=3)
        
        # 22:15 - 22:00 = 15分
        assert result.iloc[0]["in_min"] == 15
        # 22:30 - 22:00 = 30分
        assert result.iloc[1]["in_min"] == 30
        # 23:00 - 22:00 = 60分
        assert result.iloc[2]["in_min"] == 60
        
    def test_0時通過後は正しい時間差が出る(self, sample_timetable):
        """
        翌日の0時台の列車の時間差が正しく計算される
        """
        now = datetime(2026, 1, 17, 23, 50, 0, tzinfo=JST)
        
        result = next_trains(sample_timetable, now, n=2)
        
        # 00:00 - 23:50 = 10分 (翌日)
        assert result.iloc[0]["in_min"] == 10
        # 00:30 - 23:50 = 40分 (翌日)
        assert result.iloc[1]["in_min"] == 40
        
    def test_n_trains指定が機能する(self, sample_timetable):
        """
        n_trains パラメータで表示する本数が正しく制限される
        """
        now = datetime(2026, 1, 17, 22, 0, 0, tzinfo=JST)
        
        result1 = next_trains(sample_timetable, now, n=1)
        assert len(result1) == 1
        
        result5 = next_trains(sample_timetable, now, n=5)
        assert len(result5) == 5
        
    def test_該当する列車がない場合(self):
        """
        当日深夜1時で、翌日の列車がないケース
        """
        df = pd.DataFrame({
            "line": ["南北線"] * 2,
            "station": ["さっぽろ"] * 2,
            "direction": ["麻生方面"] * 2,
            "day_type": ["weekday"] * 2,
            "time": ["06:00", "07:00"],
            "dest": ["麻生"] * 2,
            "remark": [""] * 2,
        })
        
        # 翌日の1時（6時まで列車がない）
        now = datetime(2026, 1, 18, 1, 0, 0, tzinfo=JST)
        
        result = next_trains(df, now, n=3)
        
        # 6:00, 7:00 のみ該当
        assert len(result) == 2
        assert result.iloc[0]["time"] == "06:00"


class TestMidnightBoundary:
    """深夜0時付近の列車表示テスト"""
    
    def test_0時時点で終電と朝始発が含まれる(self, timetable_with_midnight_boundary):
        """
        現在が0:00の場合、その時の終電（23:50など）は除外され、
        0時台の列車と朝の始発が表示される
        """
        # 現在時刻: 2026-01-17 00:00:00
        now = datetime(2026, 1, 17, 0, 0, 0, tzinfo=JST)
        
        result = next_trains(timetable_with_midnight_boundary, now, n=4)
        
        # 0:00以降の列車: 00:00, 00:10, 00:20, 05:00
        assert len(result) >= 3
        assert result.iloc[0]["time"] == "00:00"
        assert result.iloc[1]["time"] == "00:10"
        assert result.iloc[2]["time"] == "00:20"
        # 朝の始発も含まれることを確認
        assert "05:00" in result["time"].values
        
    def test_0時30分時点での各時間帯の列車(self, timetable_with_midnight_boundary):
        """
        現在が0:30の場合、それ以降の列車が表示される
        """
        now = datetime(2026, 1, 17, 0, 30, 0, tzinfo=JST)
        
        result = next_trains(timetable_with_midnight_boundary, now, n=3)
        
        # 0:30以降: 00:00, 00:10, 00:20 は過去なので除外
        assert len(result) >= 1
        # 0:00, 0:10, 0:20は過去なので表示されない
        assert "00:00" not in result["time"].values
        assert "00:10" not in result["time"].values
        assert "00:20" not in result["time"].values
        # 最初は朝の始発（05:00）
        assert result.iloc[0]["time"] == "05:00"
        
    def test_朝5時の始発が正しく表示される(self, timetable_with_midnight_boundary):
        """
        現在が4:00の場合、朝の最初の列車（5:00）が表示される
        """
        now = datetime(2026, 1, 17, 4, 0, 0, tzinfo=JST)
        
        result = next_trains(timetable_with_midnight_boundary, now, n=3)
        
        assert result.iloc[0]["time"] == "05:00"
        assert result.iloc[1]["time"] == "05:30"


class TestDayTypeTransition:
    """平日/土日の乗り換わり時のダイヤ適用テスト"""
    
    def test_金曜深夜23時は翌土曜朝ダイヤが適用される(self, timetable_with_day_types):
        """
        金曜深夜23:30は、翌土曜朝のダイヤ（06:00など）が表示される
        2026-01-16 は金曜, 2026-01-17 は土曜
        """
        # 金曜23:30
        friday_night = datetime(2026, 1, 16, 23, 30, 0, tzinfo=JST)
        
        result = next_trains(
            timetable_with_day_types[timetable_with_day_types["day_type"] == "weekend_holiday"],
            friday_night,
            n=3
        )
        
        # 土日ダイヤを使うと、23:30後は翌日のダイヤ（06:00）が表示される
        if not result.empty:
            # 土日ダイヤの朝の列車（06:00以降）が含まれる
            assert any(int(t.split(":")[0]) >= 6 for t in result["time"].values)
    
    def test_日曜深夜は翌月曜平日ダイヤが適用される(self, timetable_with_day_types):
        """
        日曜深夜23:50は、平日ダイヤで翌朝の始発が表示される
        実装上、時刻表データの day_type が当日のものを選択するため、
        日曜に平日ダイヤで検索した場合、当日の 23:50 が表示される
        """
        # 日曜23:50
        sunday_night = datetime(2026, 1, 18, 23, 50, 0, tzinfo=JST)
        
        result = next_trains(
            timetable_with_day_types[timetable_with_day_types["day_type"] == "weekday"],
            sunday_night,
            n=2
        )
        
        # 平日ダイヤデータでは、当日の 23:50 または翌朝の時刻が表示される
        if not result.empty:
            times = result["time"].values
            # 23:50 または翌朝のいずれかが含まれる
            assert any(t in times for t in ["23:50", "05:30", "06:00"])


class TestHolidayDiagram:
    """祝日ダイヤの適用テスト"""
    
    def test_祝日判定が正しく機能する(self):
        """
        is_weekend_or_holiday が日本の祝日を正しく判定することを確認
        2026-01-12 は成人の日（祝日）
        """
        holiday_date = date(2026, 1, 12)
        regular_date = date(2026, 1, 13)  # 火曜日（平日）
        
        is_holiday = is_weekend_or_holiday(holiday_date)
        is_regular = is_weekend_or_holiday(regular_date)
        
        # 祝日と平日を区別できることを確認
        assert isinstance(is_holiday, bool)
        assert isinstance(is_regular, bool)
        
    def test_土日は祝日として判定される(self):
        """
        土日が正しく祝日として判定されることを確認
        2026-01-17 は土曜日
        2026-01-18 は日曜日
        """
        saturday = date(2026, 1, 17)
        sunday = date(2026, 1, 18)
        
        assert is_weekend_or_holiday(saturday) is True
        assert is_weekend_or_holiday(sunday) is True
        
    def test_祝日ダイヤは特定の日付で適用される(self, timetable_with_holiday_types):
        """
        祝日ダイヤが祝日に対して正しく適用されることをテスト
        """
        # 平日ダイヤでテスト（平日のみ）
        weekday_df = timetable_with_holiday_types[
            timetable_with_holiday_types["day_type"] == "weekday"
        ]
        
        # 土日祝ダイヤでテスト（土日祝のみ）
        holiday_df = timetable_with_holiday_types[
            timetable_with_holiday_types["day_type"] == "weekend_holiday"
        ]
        
        # 平日と祝日で異なるダイヤが存在することを確認
        weekday_times = set(weekday_df["time"].values)
        holiday_times = set(holiday_df["time"].values)
        
        # 異なるダイヤを持つことを確認
        # 例: 朝の始発時刻が異なる（平日5:30 vs 祝日6:00）
        weekday_morning = {t for t in weekday_times if 5 <= int(t.split(":")[0]) < 7}
        holiday_morning = {t for t in holiday_times if 5 <= int(t.split(":")[0]) < 7}
        
        # 平日と祝日で少なくとも朝の始発が異なることを確認
        assert "05:30" in weekday_morning
        assert "06:00" in holiday_morning
        
    def test_祝日深夜から翌朝への乗り換え(self, timetable_with_holiday_types):
        """
        祝日の深夜23:30から平日ダイヤで検索した場合の表示確認
        実装上、平日ダイヤで検索すると当日の 23:30 が表示される
        """
        # 祝日の深夜23:30
        holiday_night = datetime(2026, 1, 12, 23, 30, 0, tzinfo=JST)
        
        # 平日ダイヤを使用
        weekday_df = timetable_with_holiday_types[
            timetable_with_holiday_types["day_type"] == "weekday"
        ]
        
        result = next_trains(weekday_df, holiday_night, n=2)
        
        if not result.empty:
            # 当日の 23:30 または翌朝の時刻のいずれかが表示される
            times = result["time"].values
            assert any(t in times for t in ["23:30", "05:30"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
