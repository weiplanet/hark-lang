"""Fun with Fractals!"""

import itertools
import math
import sys
from dataclasses import dataclass

from PIL import Image, ImageDraw


@dataclass
class Params:
    axiom: str
    rules: dict
    iterations: int
    angle: int
    size: int = 8


# From https://elc.github.io/posts/plotting-fractals-step-by-step-with-python/#code
class Fractals:
    three_dragon = Params(
        # --
        axiom="FX+FX+FX",
        rules={"X": "X+YF+", "Y": "-FX-Y"},
        iterations=7,
        angle=90,
    )

    twin_dragon = Params(
        # --
        axiom="FX+FX",
        rules={"X": "X+YF+", "Y": "-FX-Y"},
        iterations=12,
        angle=90,
    )

    koch = Params(
        # --
        axiom="F--F--F",
        rules={"F": "F+F--F+F"},
        iterations=4,
        angle=60,
    )

    triangle = Params(
        # --
        axiom="F+F+F",
        rules={"F": "F-F+F"},
        iterations=6,
        angle=120,
        size=14,
    )


@dataclass
class Turtle:
    """A minimal turtle-like drawing interface"""

    Degrees = float

    draw: ImageDraw
    colour: tuple
    pos_x: int = 0
    pos_y: int = 0
    angle: Degrees = 0
    width: int = 1
    pen_down: bool = True
    max_x: int = 0
    max_y: int = 0
    min_x: int = 0
    min_y: int = 0

    def forward(self, dist):
        """Move forward by dist, drawing a line in the process"""
        start = (self.pos_x, self.pos_y)
        self.pos_x += dist * math.cos(math.radians(self.angle))
        self.pos_y += dist * math.sin(math.radians(self.angle))
        if self.pos_x > self.max_x:
            self.max_x = self.pos_x
        if self.pos_y > self.max_y:
            self.max_y = self.pos_y
        if self.pos_x < self.min_x:
            self.min_x = self.pos_x
        if self.pos_y < self.min_y:
            self.min_y = self.pos_y
        end = (self.pos_x, self.pos_y)
        if self.pen_down:
            self.draw.line([start, end], fill=self.colour, width=self.width)

    def right(self, angle: Degrees):
        """Turn left by ANGLE degrees"""
        prev = self.angle
        self.angle = (self.angle + angle) % 360.0
        # print(f"RIGHT | {prev} + {angle} = {self.angle}")

    def left(self, angle: Degrees):
        """Turn left by ANGLE degrees"""
        prev = self.angle
        self.angle = self.angle - angle
        if self.angle < 0:
            self.angle += 360.0
        # print(f"LEFT  | {prev} - {angle} = {self.angle}")


# https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html
def test_pillow(width=200, height=200):
    """Draw an X on a gray background and print to stdout"""
    # Modes: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
    im = Image.new("RGBA", (width, height), (128, 128, 128))
    draw = ImageDraw.Draw(im)

    teal_colour = (10, 100, 100)
    draw.line((0, 0) + im.size, fill=teal_colour)
    draw.line((0, im.size[1], im.size[0], 0), fill=teal_colour)

    # https://github.com/lincolnloop/python-qrcode/issues/66
    im.save(sys.stdout.buffer, "PNG")


def test_turtle(width=200, height=200):
    """Draw a bit"""
    im = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    t = Turtle(draw, colour=(10, 240, 240))
    t.right(45)
    t.forward(100)
    t.left(45)
    t.forward(100)
    t.left(90)
    t.forward(50)
    im.save(sys.stdout.buffer, "PNG")


def create_l_system(iters, axiom, rules) -> str:
    """Build the complete L-System sequence"""
    if iters == 0:
        return axiom

    end_string = ""
    start_string = axiom

    for _ in range(iters):
        end_string = "".join(rules[i] if i in rules else i for i in start_string)
        start_string = end_string

    return end_string


# Generate some colours
SAT = 256
VAL = 256
NUM_COLOURS = 10
COLOURS_HSV = list((x, SAT, VAL) for x in range(0, 360, int(360 / NUM_COLOURS)))


def draw_l_system(t: Turtle, instructions: str, angle: Turtle.Degrees, distance: float):
    """Draw the L-System"""
    colours = itertools.cycle(COLOURS_HSV)
    colour_period = math.ceil(len(instructions) / NUM_COLOURS)

    for step, cmd in enumerate(instructions):
        # cycle through colours
        if (step % colour_period) == 0:
            t.colour = next(colours)

        if cmd == "F":
            t.forward(distance)
        elif cmd == "+":
            t.right(angle)
        elif cmd == "-":
            t.left(angle)


def draw_fractal(fractal, linewidth=2, margin=20) -> Image:
    descr = create_l_system(fractal.iterations, fractal.axiom, fractal.rules)

    # Walk the fractal once without drawing it, so we can get dimensions
    t = Turtle(None, None, angle=0)
    t.pen_down = False
    draw_l_system(t, descr, fractal.angle, fractal.size)

    # Calculate the required image dimensions and pen offset
    final_width = int((abs(t.max_x) + abs(t.min_x)) + margin)
    final_height = int((abs(t.max_y) + abs(t.min_y)) + margin)
    start_x = abs(t.min_x) + margin / 2
    start_y = abs(t.min_y) + margin / 2

    # Oversample to reduce anti-aliasing and make things look nicer
    oversampling = 10
    width = int(final_width * oversampling)
    height = int(final_height * oversampling)

    # Create output image
    im = Image.new("HSV", (width, height), (0, 0, 0))

    # And draw it!
    t = Turtle(
        ImageDraw.Draw(im),
        COLOURS_HSV[0],
        pos_x=start_x * oversampling,
        pos_y=start_y * oversampling,
        angle=0,
        width=linewidth * oversampling,
    )
    draw_l_system(t, descr, fractal.angle, fractal.size * oversampling)

    # Scale back down
    im = im.resize((final_width, final_height), resample=Image.BILINEAR)
    im = im.convert("RGB")
    return im


def test_fracal():
    im = draw_fractal(Fractals.koch)
    # draw_fractal(Fractals.triangle)

    im.save(sys.stdout.buffer, "PNG")


def save_fractal(fractal, dest):
    im = draw_fractal(fractal)
    im.save(dest)


def main():
    # test_fracal()
    save_fractal(Fractals.triangle, "foo2.png")


if __name__ == "__main__":
    main()