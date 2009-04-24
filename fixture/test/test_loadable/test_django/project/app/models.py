from django.db import models

# Create your models here.

class NoRelations(models.Model):
    char = models.CharField(max_length=10)
    num = models.IntegerField()
    
class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return u"%s %s" % (self.first_name, self.last_name)

class Book(models.Model):
    title = models.CharField(max_length=10)
    author = models.ForeignKey(Author, related_name='books')
    
    def __unicode__(self):
        return u"%s, %s" % (self.title, self.author)

class Reviewer(models.Model):
    name = models.CharField(max_length=100)
    reviewed = models.ManyToManyField(Book, related_name='reviewers')
    
    def __unicode__(self):
        return u"%s" % (self.name)