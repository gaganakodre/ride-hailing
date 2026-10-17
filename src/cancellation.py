from datetime import timedelta


class TimeBasedCancellationPolicy:
    """Free to cancel within a short window after booking; a flat fee after that.

    Kept as its own class so the rule can be swapped (e.g. a fee based on how far the
    driver has already travelled) without changing RideService.
    """

    def __init__(self, free_window_minutes, fee):
        self.free_window = timedelta(minutes=free_window_minutes)
        self.fee = fee

    def fee_for(self, ride, cancelled_at):
        if cancelled_at - ride.created_at <= self.free_window:
            return 0
        return self.fee