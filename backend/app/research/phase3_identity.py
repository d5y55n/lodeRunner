"""Conservative time-event identity shared by overlapping research configurations."""
from .models import identity


def event_id(symbol, timeframe, decision_time):
    # All price zones observed at the same decision close share a market event.
    # This intentionally collapses simultaneous but spatially distinct zones.
    return identity({"schema":"market-close-event-v1","symbol":symbol,
                     "timeframe":timeframe,"decision_time":decision_time})


def interaction_id(candidate_id, configuration_id, start, number):
    return identity(["zone-visit-v1",candidate_id,configuration_id,start,number])


def measurement_id(underlying_event_id, interaction, configuration, direction,tp,sl,horizon):
    return identity(["outcome-v1",underlying_event_id,interaction,configuration,direction,tp,sl,horizon])
