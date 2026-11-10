from dataclasses import dataclass
@dataclass
class Candle:
    open_time:int; open:float; high:float; low:float; close:float; volume:float
@dataclass
class Zone:
    source_tf:str; upper:float; lower:float; strength:float; age:int; start_time:int; source_index:int
@dataclass
class Tap:
    index:int; time:int; price:float; rsi:float
@dataclass
class Signal:
    symbol:str; execution_tf:str; direction:str; zone:Zone; tap_number:int; tap:Tap
