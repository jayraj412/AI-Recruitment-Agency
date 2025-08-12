import datetime
import pytz

# Import the class from your scheduler.py file
from meeting_scheduler import MeetingScheduler, TIMEZONE

def main():
    """
    This is the main script to define meeting details and schedule it.
    """
    # --- DEFINE YOUR MEETING DETAILS HERE ---
    summary = "Quarterly Business Review"
    description = "Review of Q3 performance and planning for Q4."
    attendees = ["b418024@iiit-bh.ac.in", "sunitamohanty.120@gmail.com"]
    
    # Set timezone
    tz = pytz.timezone(TIMEZONE)

    # Set start and end times (e.g., August 5, 2025, from 2:00 PM to 3:30 PM)
    start_time = tz.localize(datetime.datetime(2025, 8, 5, 14, 0, 0))
    end_time = tz.localize(datetime.datetime(2025, 8, 5, 15, 30, 0))

    # --- SCHEDULING ---
    # 1. Create an instance of the MeetingScheduler class
    scheduler = MeetingScheduler(
        summary=summary,
        description=description,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees
    )
    
    # 2. Call the schedule method to create the event
    scheduler.schedule()


if __name__ == "__main__":
    main()