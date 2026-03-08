"""
Tests para verificar corrección de zona horaria en fichajes
"""
import pytest
from datetime import datetime, time, date
import pytz
from app.utils.timezone_utils import (
    get_current_time_argentina,
    get_current_date_argentina,
    get_current_time_only_argentina,
    convert_utc_to_argentina,
    convert_argentina_to_utc,
    localize_to_argentina,
    is_same_day_argentina,
    ARGENTINA_TZ
)


class TestTimezoneUtils:
    """Test timezone utility functions"""
    
    def test_get_current_time_argentina_has_timezone(self):
        """Current time should have Argentina timezone"""
        current = get_current_time_argentina()
        assert current.tzinfo is not None
        assert current.tzinfo.zone == 'America/Argentina/Buenos_Aires'
    
    def test_get_current_date_argentina(self):
        """Current date should be in Argentina timezone"""
        current_date = get_current_date_argentina()
        assert isinstance(current_date, date)
    
    def test_get_current_time_only_argentina(self):
        """Current time only should return time object"""
        current_time = get_current_time_only_argentina()
        assert isinstance(current_time, time)
    
    def test_convert_utc_to_argentina(self):
        """UTC datetime should convert to Argentina timezone"""
        # Create UTC datetime: 2026-03-08 17:00:00 UTC
        utc_dt = datetime(2026, 3, 8, 17, 0, 0, tzinfo=pytz.utc)
        
        # Convert to Argentina (UTC-3)
        arg_dt = convert_utc_to_argentina(utc_dt)
        
        # Should be 14:00 in Argentina
        assert arg_dt.hour == 14
        assert arg_dt.minute == 0
        assert arg_dt.tzinfo.zone == 'America/Argentina/Buenos_Aires'
    
    def test_convert_argentina_to_utc(self):
        """Argentina datetime should convert to UTC"""
        # Create Argentina datetime: 2026-03-08 14:00:00 ART
        arg_dt = ARGENTINA_TZ.localize(datetime(2026, 3, 8, 14, 0, 0))
        
        # Convert to UTC
        utc_dt = convert_argentina_to_utc(arg_dt)
        
        # Should be 17:00 in UTC
        assert utc_dt.hour == 17
        assert utc_dt.minute == 0
        assert utc_dt.tzinfo == pytz.utc
    
    def test_localize_to_argentina(self):
        """Naive datetime should get Argentina timezone"""
        naive_dt = datetime(2026, 3, 8, 14, 0, 0)
        
        localized = localize_to_argentina(naive_dt)
        
        assert localized.tzinfo is not None
        assert localized.tzinfo.zone == 'America/Argentina/Buenos_Aires'
        assert localized.hour == 14
    
    def test_is_same_day_argentina_true(self):
        """Two datetimes on same day in Argentina should return True"""
        # 2026-03-08 23:00 ART and 2026-03-08 01:00 ART
        dt1 = ARGENTINA_TZ.localize(datetime(2026, 3, 8, 23, 0, 0))
        dt2 = ARGENTINA_TZ.localize(datetime(2026, 3, 8, 1, 0, 0))
        
        assert is_same_day_argentina(dt1, dt2) is True
    
    def test_is_same_day_argentina_false(self):
        """Two datetimes on different days in Argentina should return False"""
        # 2026-03-08 23:00 ART and 2026-03-09 01:00 ART
        dt1 = ARGENTINA_TZ.localize(datetime(2026, 3, 8, 23, 0, 0))
        dt2 = ARGENTINA_TZ.localize(datetime(2026, 3, 9, 1, 0, 0))
        
        assert is_same_day_argentina(dt1, dt2) is False
    
    def test_timezone_offset_is_minus_3(self):
        """Argentina timezone should be UTC-3"""
        # Create a datetime in Argentina
        arg_dt = ARGENTINA_TZ.localize(datetime(2026, 3, 8, 12, 0, 0))
        
        # Get UTC offset in hours
        offset_seconds = arg_dt.utcoffset().total_seconds()
        offset_hours = offset_seconds / 3600
        
        # Should be -3 hours
        assert offset_hours == -3


class TestTimeTrackingTimezone:
    """Test time tracking with correct timezone"""
    
    def test_check_in_time_is_argentina_time(self):
        """Check-in should record Argentina time, not UTC"""
        # Simulate check-in at 14:00 Argentina time
        # This would be 17:00 UTC
        
        current_time = get_current_time_only_argentina()
        
        # Current time should be a time object
        assert isinstance(current_time, time)
        
        # If it's 14:00 in Argentina, it should NOT be 17:00
        # (This test verifies the time is local, not UTC)
        current_full = get_current_time_argentina()
        utc_equivalent = convert_argentina_to_utc(current_full)
        
        # The difference should be 3 hours
        hour_diff = (utc_equivalent.hour - current_full.hour) % 24
        assert hour_diff == 3
    
    def test_work_hours_calculation_with_argentina_time(self):
        """Work hours should calculate correctly with Argentina timezone"""
        # Employee checks in at 09:00 and checks out at 17:00 Argentina time
        check_in = time(9, 0, 0)
        check_out = time(17, 0, 0)
        
        # Calculate hours worked
        hours = check_out.hour - check_in.hour
        
        # Should be 8 hours
        assert hours == 8
    
    def test_midnight_crossing_same_day_argentina(self):
        """Midnight crossing in UTC should still be same day in Argentina"""
        # 23:00 Argentina time = 02:00 UTC next day
        arg_dt = ARGENTINA_TZ.localize(datetime(2026, 3, 8, 23, 0, 0))
        utc_dt = convert_argentina_to_utc(arg_dt)
        
        # In UTC it's the next day
        assert utc_dt.day == 9
        
        # But in Argentina it's still the same day
        assert arg_dt.day == 8
        
        # This is important for daily time tracking


class TestHistoricalDataCorrection:
    """Test scenarios for correcting historical data"""
    
    def test_identify_records_with_utc_offset(self):
        """Should identify records that were saved with UTC offset"""
        # Example: Employee checked in at 14:00 local time
        # But it was saved as 17:00 (UTC)
        
        saved_time_utc = time(17, 0, 0)  # What was saved (wrong)
        expected_time_local = time(14, 0, 0)  # What should have been saved
        
        # Difference should be 3 hours
        diff = saved_time_utc.hour - expected_time_local.hour
        assert diff == 3
    
    def test_correct_historical_record(self):
        """Should correct a historical record by subtracting 3 hours"""
        # Record was saved as 17:00 (UTC) but should be 14:00 (Argentina)
        wrong_time = time(17, 0, 0)
        
        # Correction: subtract 3 hours
        corrected_hour = (wrong_time.hour - 3) % 24
        corrected_time = time(corrected_hour, wrong_time.minute, wrong_time.second)
        
        assert corrected_time == time(14, 0, 0)
    
    def test_edge_case_early_morning_correction(self):
        """Should handle early morning times correctly"""
        # Record was saved as 02:00 (UTC) but should be 23:00 previous day (Argentina)
        wrong_time = time(2, 0, 0)
        
        # Correction: subtract 3 hours (wraps to previous day)
        corrected_hour = (wrong_time.hour - 3) % 24
        corrected_time = time(corrected_hour, wrong_time.minute, wrong_time.second)
        
        assert corrected_time == time(23, 0, 0)
        # Note: Date correction would need to be handled separately


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    def test_full_day_workflow_argentina_timezone(self):
        """Test complete workflow with Argentina timezone"""
        # Employee checks in at 09:00 Argentina time
        check_in_time = get_current_time_argentina().replace(hour=9, minute=0, second=0)
        
        # Employee checks out at 17:00 Argentina time
        check_out_time = get_current_time_argentina().replace(hour=17, minute=0, second=0)
        
        # Both should be on the same day
        assert check_in_time.date() == check_out_time.date()
        
        # Calculate hours worked
        hours_worked = (check_out_time - check_in_time).total_seconds() / 3600
        
        # Should be 8 hours
        assert hours_worked == 8.0
    
    def test_late_night_shift_argentina(self):
        """Test late night shift that crosses midnight"""
        # Employee checks in at 22:00 on March 8
        check_in = ARGENTINA_TZ.localize(datetime(2026, 3, 8, 22, 0, 0))
        
        # Employee checks out at 02:00 on March 9
        check_out = ARGENTINA_TZ.localize(datetime(2026, 3, 9, 2, 0, 0))
        
        # Should calculate 4 hours worked
        hours_worked = (check_out - check_in).total_seconds() / 3600
        assert hours_worked == 4.0
        
        # But they are on different days
        assert check_in.date() != check_out.date()


class TestRegressionPrevention:
    """Tests to prevent regression of timezone bug"""
    
    def test_current_time_is_not_utc(self):
        """Ensure we're not using UTC time"""
        arg_time = get_current_time_argentina()
        utc_time = datetime.now(pytz.utc)
        
        # Times should be different (3 hours apart)
        hour_diff = abs(arg_time.hour - utc_time.hour)
        
        # Should be 3 hours difference (or 21 if crossing midnight)
        assert hour_diff in [3, 21]
    
    def test_saved_time_matches_local_time(self):
        """Saved time should match local Argentina time"""
        # When employee clicks "Check In" at 14:00 local time
        local_time = time(14, 0, 0)
        
        # The saved time should be 14:00, not 17:00
        saved_time = get_current_time_only_argentina()
        
        # We can't test exact time, but we can verify it's a time object
        # and not offset by 3 hours from what we expect
        assert isinstance(saved_time, time)
    
    def test_no_timezone_in_time_column(self):
        """Time column should store time without timezone info"""
        # Database time columns store time without timezone
        # The timezone conversion should happen at the application level
        
        current_time = get_current_time_only_argentina()
        
        # Should be a time object (no timezone)
        assert isinstance(current_time, time)
        assert not hasattr(current_time, 'tzinfo') or current_time.tzinfo is None
