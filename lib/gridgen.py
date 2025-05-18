from .commonsense import IntPoint
from typing       import Literal, Generator


def grid(
        start:     IntPoint,
        interval:  int,
        direction: Literal['horizontal', 'vertical'] = 'horizontal'
        ) -> Generator[IntPoint, None, None]:
    
    i = 0

    while True:
        yield IntPoint(
            start.x + interval * i * (direction == 'horizontal'),
            start.y + interval * i * (direction == 'vertical')
        )
        i += 1