
from fixture import DataSet

__all__ = ['EntryData', 'CommentData']

class EntryData(DataSet):
    class great_monday:
        title = "Monday Was Great"
        body = """\
Monday was the best day ever.  I got up (a little late, but that's OK) then I ground some coffee.  Mmmm ... coffee!  I love coffee.  Do you know about <a href="http://www.metropoliscoffee.com/">Metropolis</a> coffee?  It's amazing.  Delicious.  I drank a beautiful cup of french pressed <a href="http://www.metropoliscoffee.com/shop/coffee/blends.php">Spice Island</a>, had a shave and went to work.  What a day!
"""

class CommentData(DataSet):
    class monday_liked_it:
        entry = EntryData.great_monday
        comment = """\
I'm so glad you have a blog because I want to know what you are doing everyday.  Heh, that sounds creepy.  What I mean is it's so COOL that you had a great Monday.  I like Mondays too.
"""
    class monday_sucked:
        entry = EntryData.great_monday
        comment = """\
Are you serious?  Mannnnnn, Monday really sucked.
"""