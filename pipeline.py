from tcms.utils.permissions import initiate_user_with_default_setups


def initiate_defaults(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        initiate_user_with_default_setups(user)
