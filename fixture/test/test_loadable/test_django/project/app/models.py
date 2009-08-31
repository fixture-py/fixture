from django.db import models
    
class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

class Book(models.Model):
    title = models.CharField(max_length=10)
    author = models.ForeignKey(Author, related_name='books')

class Reviewer(models.Model):
    name = models.CharField(max_length=100)
    reviewed = models.ManyToManyField(Book, related_name='reviewers')
