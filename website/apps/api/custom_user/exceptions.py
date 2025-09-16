class NoTrialSubscriptionExists(Exception):
    pass


class AlreadySubscribedError(Exception):
    pass


class SubscriptionDisabledError(Exception):
    pass


class SubscriptionCanceledError(Exception):
    pass
