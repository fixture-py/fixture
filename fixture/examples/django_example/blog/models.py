from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Category(models.Model):
    title = models.CharField(_('title'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)

    def __unicode__(self):
        return u'%s' % self.title


class Post(models.Model):
    title = models.CharField(_('title'), max_length=200)
    author = models.ForeignKey(User, blank=True, null=True)
    body = models.TextField(_('body'))
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    categories = models.ManyToManyField(Category, blank=True)

    def __unicode__(self):
        return u'%s' % self.title
