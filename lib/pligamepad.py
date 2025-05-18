#############################
##  ПРИГОТОВЬТЕ СВОЙ ЗАД!  ##
#############################


from threading import Thread
from inputs    import get_gamepad, InputEvent


class EventType:
    ABSOLUTE = 'Absolute'
    KEY      = 'Key'
    SYNC     = 'Sync'


STK_ABS_LIM = 32767
TRG_ABS_LIM = 1023


class Stick:

    def __init__(self) -> None:
        self._x: float = 0.0
        self._y: float = 0.0

    @property
    def x(self) -> float:
        return self._x
    @property
    def y(self) -> float:
        return self._y
    
    @x.setter
    def x(self, value: int) -> None:
        self._x = max(-1.0, min(1.0, value / STK_ABS_LIM))
    @y.setter
    def y(self, value: int) -> None:
        self._y = max(-1.0, min(1.0, value / STK_ABS_LIM))
    
    def __bool__(self) -> bool:
        return self._x > 0.01 or self._y > 0.01
    
    def __repr__(self) -> str:
        return f'({self.x}, {self.y})'


class Trigger:

    def __init__(self) -> None:
        self._value: float = 0.0

    @property
    def value(self) -> float:
        return self._value
    
    @value.setter
    def value(self, value: int) -> None:
        self._value = min(1.0, value / TRG_ABS_LIM)

    def __bool__(self) -> bool:
        return self._value > 0.01
    
    def __repr__(self) -> str:
        return f'{self.value}'


class Key:

    def __init__(self) -> None:
        self._state: bool = False

    @property
    def state(self) -> bool:
        return self._state
    
    def __bool__(self) -> bool:
        return self.state
    
    def __repr__(self) -> str:
        return str(bool(self))
    

class DPad:

    def __init__(self) -> None:
        self._x: int = 0
        self._y: int = 0

    @property
    def x(self) -> int:
        return self._x
    @property
    def y(self) -> int:
        return self._y
    
    def __bool__(self) -> bool:
        return self._x > 1 or self._y > 1
    
    def __repr__(self) -> str:
        return f'({self.x}, {self.y})'


class StickSet:
    def __init__(self) -> None:
        self.left  = Stick()
        self.right = Stick()


class ThumbSet:
    def __init__(self) -> None:
        self.left  = Key()
        self.right = Key()


class KeySet:
    def __init__(self) -> None:
        self.mode   = Key()
        self.select = Key()
        self.start  = Key()
        self.a      = Key()
        self.b      = Key()
        self.x      = Key()
        self.y      = Key()


class BumperSet:
    def __init__(self) -> None:
        self.left  = Key()
        self.right = Key()


class TriggerSet:
    def __init__(self) -> None:
        self.left  = Trigger()
        self.right = Trigger()


class GamepadListener:

    def __init__(self) -> None:

        self._thread = None
        self._is_running = False

        self.registered = False

        self.bumper  = BumperSet()
        self.dpad    = DPad()
        self.key     = KeySet()
        self.stick   = StickSet()
        self.thumb   = ThumbSet()
        self.trigger = TriggerSet()

    def start(self) -> None:

        self._is_running = True

        self._thread = Thread(
            target = self._updater,
            args   = (),
            name   = self.__class__.__name__,
            daemon = True
        )
        self._thread.start()

    def stop(self) -> None:

        self._is_running = False

    def _updater(self) -> None:

        while self._is_running:

            event: InputEvent = get_gamepad()[0]

            self.registered = True

            if event.ev_type == EventType.KEY:

                match event.code:
                    case 'BTN_TL':     self.bumper.left._state  = bool(event.state)
                    case 'BTN_TR':     self.bumper.right._state = bool(event.state)
                    case 'BTN_MODE':   self.key.mode._state     = bool(event.state)
                    case 'BTN_SELECT': self.key.select._state   = bool(event.state)
                    case 'BTN_START':  self.key.start._state    = bool(event.state)
                    case 'BTN_SOUTH':  self.key.a._state        = bool(event.state)
                    case 'BTN_EAST':   self.key.b._state        = bool(event.state)
                    case 'BTN_NORTH':  self.key.x._state        = bool(event.state)
                    case 'BTN_WEST':   self.key.y._state        = bool(event.state)
                    case 'BTN_THUMBL': self.thumb.left._state   = bool(event.state)
                    case 'BTN_THUMBR': self.thumb.right._state  = bool(event.state)

            elif event.ev_type == EventType.ABSOLUTE:

                match event.code:
                    case 'ABS_HAT0X': self.dpad._x             = event.state
                    case 'ABS_HAT0Y': self.dpad._y             = event.state
                    case 'ABS_X':     self.stick.left.x        = event.state
                    case 'ABS_Y':     self.stick.left.y        = event.state
                    case 'ABS_RX':    self.stick.right.x       = event.state
                    case 'ABS_RY':    self.stick.right.y       = event.state
                    case 'ABS_Z':     self.trigger.left.value  = event.state
                    case 'ABS_RZ':    self.trigger.right.value = event.state


if __name__ == '__main__':
    from time import sleep
    gamepad = GamepadListener()
    gamepad.start()
    try:
        while True:
            print(
                gamepad.stick.left,
                gamepad.stick.right,
                gamepad.trigger.left,
                gamepad.trigger.right,
                gamepad.key.a,
                bool(gamepad.stick.right)
            )
            sleep(0.1)
    except KeyboardInterrupt:
        gamepad.stop()