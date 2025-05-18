from typing import Iterator


class IntPoint:
		'''
		Simple mutable 2-dimensional vector.
		'''
		def __init__(self, x: int, y: int) -> None:
			self.x = x
			self.y = y
			
		def __iter__(self) -> Iterator[int]:
			return iter([self.x, self.y])