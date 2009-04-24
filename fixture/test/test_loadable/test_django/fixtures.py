from fixture import DataSet, style

class ValidNoRelationsData(DataSet):
    class one:
        char = "one"
        num = 1
    class two:
        char = "two"
        num = 2

class InvalidNoRelationsData(DataSet):
    class one:
        char = "one"
        invalid = 'test'
    class two:
        char = "two"
        some_other = 2

class app__Author(DataSet):
    class frank_herbert:
        first_name = "Frank"
        last_name = "Herbert"
    class guido:
        first_name = "Guido"
        last_name = "Van rossum"
        
class app__Book(DataSet):
    class dune:
        title = "Dune"
        author = app__Author.frank_herbert
    
    class python:
        title = 'Python'
        author = app__Author.guido
        
class app__Reviewer(DataSet):
    class ben:
        name = 'ben'
        reviewed = [app__Book.dune, app__Book.python]

class DjangoDataSetWithMeta(DataSet):
    class Meta:
        django_model = 'app.Author'
    class frank_herbert:
        first_name = "Frank"
        last_name = "Herbert"
    class guido:
        first_name = "Guido"
        last_name = "Van rossum"