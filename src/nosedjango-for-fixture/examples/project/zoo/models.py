from django.db import models

"""
Module-level doctest.

    >>> Zoo
    <class 'project.zoo.models.Zoo'>
    >>> 1 + 1
    2
"""

def func():
    """
    Function-level test
        >>> 1+3
        4
    """
    pass
# Create your models here.
class Zoo(models.Model):
    """
    Class-level doctest

    >>> Zoo
    <class 'project.zoo.models.Zoo'>
    >>> 1 + 1
    2
    >>> Zoo.objects.all()
    []
    >>> z = Zoo(name='Bronx')
    >>> z.save()
    >>> z
    <Zoo: Bronx>
    >>> Zoo.objects.all()
    [<Zoo: Bronx>]
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        """
        Function in class test
        >>> 1 + 2
        3
        """
        return self.name

