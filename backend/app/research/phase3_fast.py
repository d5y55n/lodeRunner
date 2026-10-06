"""Array-backed Phase 2 interaction semantics, checked against the reference engine."""
import numpy as np
from .interactions import Interaction,ExitRule,side
from .models import validate_candles


class CandleArrays:
    def __init__(self,candles):
        validate_candles(candles)
        self.candles=candles
        for field in ("start","end","open","high","low","close"):
            setattr(self,field,np.array([getattr(c,field) for c in candles]))

    def visits(self,zone,rule=ExitRule()):
        a=self
        n=len(a.candles)
        overlap=(a.high>=zone.lower)&(a.low<=zone.upper)
        touched=np.flatnonzero(overlap&(a.start>=zone.candidate.known_at))
        sep=zone.candidate.price*rule.separation_fraction
        exits=np.flatnonzero((a.close>zone.upper+sep)|(a.close<zone.lower-sep))
        result=[];cursor=0
        while cursor<len(touched):
            i=int(touched[cursor]);position=np.searchsorted(exits,i)
            j=int(exits[position]) if position<len(exits) else n-1
            ended=position<len(exits)
            approach=side(float(a.close[i-1] if i else a.open[i]),zone)
            v=Interaction(zone.id,len(result)+1,int(a.start[i]),int(a.end[i]),float(a.close[i]),approach)
            v.transitions=[("OUTSIDE",v.start),("ENTERED",v.observed_at)]
            if j>i:v.transitions.append(("INTERACTING",int(a.end[i+1])));v.state="INTERACTING"
            v.candles_spent=j-i+1
            sl=slice(i,j+1);hits=overlap[sl]
            op=a.open[sl];cl=a.close[sl];lo=a.low[sl];hi=a.high[sl]
            wick=((lo<np.minimum(op,cl))&(lo<=zone.upper)&(np.minimum(op,cl)>=zone.lower))|((hi>np.maximum(op,cl))&(hi>=zone.lower)&(np.maximum(op,cl)<=zone.upper))
            v.wick_touched=bool(np.any(wick&hits))
            v.close_entered=bool(np.any((cl>=zone.lower)&(cl<=zone.upper)&hits))
            if approach=="INSIDE":
                v.max_penetration_price=v.max_penetration_zone_fraction=v.crossed_through=None
            else:
                penetration=zone.upper-lo[hits] if approach=="ABOVE" else hi[hits]-zone.lower
                v.max_penetration_price=max(0.,float(penetration.max()))
                v.max_penetration_zone_fraction=v.max_penetration_price/(zone.upper-zone.lower)
                v.crossed_through=bool(np.any(cl<zone.lower) if approach=="ABOVE" else np.any(cl>zone.upper))
            if ended:
                v.end=int(a.end[j]);v.exit_direction=side(float(a.close[j]),zone);v.state="EXITED"
                v.transitions.append(("EXITED",v.end))
            result.append(v)
            cursor=int(np.searchsorted(touched,j+1))
        return result

    def visit_indices(self,zone,rule=ExitRule()):
        """Vectorized entry/exit indices with exactly the reference visit boundaries."""
        touched=np.flatnonzero((self.high>=zone.lower)&(self.low<=zone.upper)&(self.start>=zone.candidate.known_at))
        if not len(touched):return []
        separation=zone.candidate.price*rule.separation_fraction
        exits=np.flatnonzero((self.close>zone.upper+separation)|(self.close<zone.lower-separation))
        positions=np.searchsorted(exits,touched)
        ended=positions<len(exits)
        endpoints=np.r_[exits,len(self.candles)-1][positions]
        starts=np.r_[True,touched[1:]>endpoints[:-1]]
        return zip(touched[starts].tolist(),endpoints[starts].tolist(),ended[starts].tolist())
