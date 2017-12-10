#!/usr/bin/env python
# coding: utf-8
"""
A tool for generation hex calendar for a year
"""

import os
import calendar
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps


MONTHS_LEFT = 30
MONTHS_TOP = 390
MONTH_HORIZONTAL_STEP = 220
MONTH_VERTICAL_STEP = 160
MONTHS_IN_ROW = 4
MONTH_DAYS_LINE_SPACING = 5
MONTH_WEEK_PADDING = 5
YEAR_TOP_PADDING = 10
YEAR_RIGHT_PADDING = 10

weekdays = {
    0: 'Mo',
    1: 'Tu',
    2: 'We',
    3: 'Th',
    4: 'Fr',
    5: 'Sa',
    6: 'Su',
}

MONDAY = 0
SUNDAY = 6


def get_weekdays(first_weekday=0):
    """Get weekdays as numbers [0..6], starting with first_weekday"""
    return list(list(range(0, 7)) * 2)[first_weekday: first_weekday + 7]


class TextObject(object):
    """Text object"""

    def __init__(self, text, x, y, font, color):
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.color = color


class MonthObject(object):
    """Month object"""

    def __init__(self, draw, year, month, **kwargs):
        """Init"""
        self.draw = draw
        self.year = year
        self.month = month
        self.month_font = kwargs['month_font']
        self.week_font = kwargs['week_font']
        self.x = kwargs['x']
        self.y = kwargs['y']
        self.month_color = kwargs['month_color']
        self.week_color = kwargs['week_color']
        self.weekend_color = kwargs['weekend_color']
        self.days_color = kwargs['days_color']
        self.first_weekday = kwargs.get('first_weekday', MONDAY)
        self.month_upper = kwargs.get('month_upper', False)
        self.week_upper = kwargs.get('week_upper', False)
        self.days_upper = kwargs.get('days_upper', False)
        self.items = []
        self._prepare(self.month_upper, self.week_upper, self.days_upper)

    def _add_month(self, x, y, color, upper=False):
        """Add month header"""
        month = '{:02x}'.format(self.month)
        if upper:
            month = month.upper()
        w, h = self.draw.textsize(month, font=self.month_font)
        text_obj = TextObject(month, x, y, self.month_font, color)
        self.items.append(text_obj)
        return w, h

    def _add_week(self, x, y, color, weekend_color, upper=False):
        """Add week"""
        space_w, space_h = self.draw.textsize(' ', font=self.week_font)
        orig_x = x
        w, h = 0, 0
        for d in get_weekdays(self.first_weekday):
            weekday_text = weekdays[d].upper() if upper else weekdays[d]
            w, h = self.draw.textsize(weekday_text, font=self.week_font)
            text_obj = TextObject(weekday_text, x, y, self.week_font, weekend_color if d in [5, 6] else color)
            x += w + space_w
            self.items.append(text_obj)
        return x - orig_x + w - space_w, h

    def _add_days(self, x, y, color, weekend_color, upper=False):
        """Add month days"""
        space_w, space_h = self.draw.textsize(' ', font=self.week_font)
        orig_x, orig_y = x, y
        h = 0
        for i, v in enumerate(calendar.Calendar().itermonthdays2(self.year, self.month)):
            day, wd = v
            day_str = '{:02x}'.format(day)
            if upper:
                day_str = day_str.upper()
            w, h = self.draw.textsize(day_str, font=self.week_font)
            if i and i % 7 == 0:
                x = 0
                y += h + MONTH_DAYS_LINE_SPACING
            if day:
                text_obj = TextObject(day_str, x, y, self.week_font, weekend_color if wd in [5, 6] else color)
                x += w + space_w
                self.items.append(text_obj)
            else:
                x += w + space_w
                continue
        return x - orig_x - space_w, y - orig_y + h

    def _prepare(self, month_upper=False, week_upper=False, days_upper=False):
        """Put all month object items together"""
        week_width, week_height = self._add_week(
            0, self.month_font.size, self.week_color, self.weekend_color, week_upper)
        month_width, _ = self.draw.textsize('{:02x}'.format(12), font=self.month_font)
        month_x, month_y = (week_width // 2) - month_width, 0 - MONTH_WEEK_PADDING
        _, month_heigth = self._add_month(month_x, month_y, self.month_color, month_upper)
        self._add_days(0, week_height * 2 + month_heigth, self.days_color, self.weekend_color, days_upper)

    def render(self):
        """Draw items"""
        for item in self.items:
            self.draw.text((self.x + item.x, self.y + item.y), item.text, font=item.font, fill=item.color)


def add_year(img, year, font, color, upper=False):
    """Add year"""
    txt_img = Image.new('RGBA', (100, 100))
    txt_img_draw = ImageDraw.Draw(txt_img)
    year_text = '{:x}'.format(year)
    if upper:
        year_text = year_text.upper()
    year_text = '0x' + year_text
    year_width, year_height = txt_img_draw.textsize(year_text, font=font)
    txt_img_draw.text((0, 0), year_text, font=font, fill=color)
    rotated_img = txt_img.rotate(90, expand=True)
    pos = (img.size[0] - txt_img.size[1] + year_width - YEAR_RIGHT_PADDING, YEAR_TOP_PADDING - year_height)
    img.paste(rotated_img, pos, rotated_img)


def add_image(img, image_path):
    """Add image"""
    if not os.path.isfile(image_path):
        print('File "{}" was not found!'.format(image_path))
        return
    image = Image.open(image_path, 'r')
    # resize image
    new_size = image.size
    while new_size[0] > img.size[0] or new_size[1] > MONTHS_TOP:
        new_size = (int(new_size[0] * 0.75), int(new_size[1] * 0.75))
    image = image.resize(new_size, Image.ANTIALIAS)
    # calculate coordinates
    x = (img.size[0] - image.size[0]) // 2
    y = (MONTHS_TOP - image.size[1]) // 2
    img.paste(image, (x, y))


def add_months(img, year, **kwargs):
    """Add months"""
    img_draw = ImageDraw.Draw(img)
    for month_index in range(1, 12 + 1):
        month_object = MonthObject(
            draw=img_draw, 
            year=year, 
            month=month_index, 
            x=MONTHS_LEFT + MONTH_HORIZONTAL_STEP * ((month_index - 1) % MONTHS_IN_ROW), 
            y=MONTHS_TOP + MONTH_VERTICAL_STEP * ((month_index - 1) // MONTHS_IN_ROW),
            **kwargs
        )
        month_object.render()


def make_hex_calendar(img, year):
    """Make Hex Calendar"""
    image_path = 'spb_python_logo.png'
    add_image(img, image_path)

    month_font = ImageFont.truetype('FreeMonoBold.ttf', 18)
    week_font = ImageFont.truetype('FreeMonoBold.ttf', 15)
    year_font = ImageFont.truetype('FreeMonoBold.ttf', 25)
    month_color = (70, 130, 180, 255)
    week_color = (70, 130, 180, 255)
    weekend_color = (255, 220, 75, 255)
    days_color = (255, 255, 255, 255)
    year_color = (80, 130, 180, 255)
    first_weekday = MONDAY
    month_upper = False
    week_upper = False
    days_upper = False

    add_months(
        img, 
        year, 
        month_font=month_font, 
        week_font=week_font, 
        month_color=month_color, 
        week_color=week_color,
        weekend_color=weekend_color, 
        days_color=days_color, 
        first_weekday=first_weekday, 
        month_upper=month_upper, 
        week_upper=week_upper, 
        days_upper=days_upper
    )

    year_upper = False
    add_year(img, year, year_font, year_color, year_upper)


def main():
    """Main"""
    width = 900
    height = 900

    img = Image.new('RGB', (width, height), 'black')

    year = 2018
    make_hex_calendar(img, year)

    img.save('hex_calendar_{}.png'.format(year))


if __name__ == '__main__':
    main()
